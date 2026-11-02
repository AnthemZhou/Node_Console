"""Capture actual native menu results and plugin snapshots in an isolated Blender.

No native result is inferred from plugin ranking. Screenshots are the oracle;
OCR interpretation is a separate, reviewable step. Run with run_isolated_blender.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_search_queries import cases

args = sys.argv[sys.argv.index('--') + 1:]
OUTPUT = Path(args[0]).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.use_translate_interface = True
spec = importlib.util.spec_from_file_location('NCAudit', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._settings_path = lambda: OUTPUT / 'test-settings.json'
nc._preferences = lambda: None
nc._refresh_asset_index()
queries = cases()
if '--cases' in args:
    queries = json.loads(Path(args[args.index('--cases') + 1]).read_text())
if '--pilot' in args:
    queries = [queries[i] for i in [0, 27, 54, 81, 108, 135]]
report = dict(version=bpy.app.version_string, build=bpy.app.build_hash.decode(),
              samples=[], catalogs={}, native_menus={}, errors=[], favorites=[], history='no executed search result')
state = dict(index=0, phase='dismiss', context=None)
multilingual = '--multilingual' in args


def write_report():
    (OUTPUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))


def tick():
    try:
        window = bpy.context.window_manager.windows[0]
        if state['phase'] == 'dismiss':
            window.event_simulate(type='ESC', value='PRESS')
            window.event_simulate(type='ESC', value='RELEASE')
            state['phase'] = 'setup'
            return 0.5
        if state['index'] == len(queries):
            write_report()
            print('AUDIT_CAPTURE_COMPLETE', len(report['samples']), flush=True)
            bpy.ops.wm.quit_blender()
            return None
        sample = queries[state['index']]
        if state['phase'] == 'setup':
            key = '|'.join(sample[k] for k in ('tree', 'engine', 'shader'))
            if multilingual:
                key += '|' + sample['language']
            area = max(window.screen.areas, key=lambda a: a.width * a.height)
            if state['context'] != key:
                old_tree = state.get('tree')
                area.type = 'NODE_EDITOR'
                space = area.spaces.active
                space.tree_type = sample['tree']
                space.show_region_ui = False
                space.pin = True
                tree = bpy.data.node_groups.new('Isolated audit', sample['tree'])
                space.node_tree = tree
                if sample['tree'] == 'ShaderNodeTree':
                    space.shader_type = sample['shader']
                bpy.context.scene.render.engine = sample['engine']
                state.update(context=key, area=area, tree=tree)
                if old_tree:
                    bpy.data.node_groups.remove(old_tree)
            region = next(r for r in area.regions if r.type == 'WINDOW')
            state['region'] = region
            bpy.context.preferences.view.language = sample['language']
            if multilingual:
                nc._search_language = lambda: sample['language']
                nc._clear_search_caches()
            state['phase'] = 'snapshot'
            return 0.4
        if state['phase'] == 'snapshot':
            key = state['context']
            area, region = state['area'], state['region']
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert area.spaces.active.edit_tree == state['tree'], 'Editor context did not settle'
                nc._rebuild_search_entries(bpy.context)
                if key not in report['catalogs']:
                    report['catalogs'][key] = [dict(id=e.identifier, english=e.english, chinese=e.chinese,
                        kind=e.kind, node=e.node_type, paths=[[i.text for i in e._native_items(language)] for language in (0, 1)],
                        raw_paths=[[row[column] for row in e.menu_paths] for column in (0, 1)],
                        weights=[[i.weight for i in e._native_items(language)] for language in (0, 1)],
                        settings=e.settings, menu=bool(e.menu_paths), hidden=e.native_hidden)
                        for e in nc.NODE_SEARCH_ENTRIES]
                menu_key = key + '|' + sample['language']
                if menu_key not in report['native_menus']:
                    # Diagnostic menu metadata only: this shares the collector's
                    # traversal limitations. Screenshots remain the native oracle.
                    class OriginalCollector(nc.node_menu_search.Collector):
                        def function(self, function):
                            return function
                    collector = OriginalCollector(bpy.context, bpy.app.translations.pgettext_iface)
                    collector.draw('NODE_MT_add', [])
                    assert not collector.errors, collector.errors
                    report['native_menus'][menu_key] = [dict(operator=op, path=sep.join(parts), weight=weight,
                        properties={k: v for k, v in vars(props).items() if k != 'settings'},
                        settings=[dict(name=s.name, value=s.value) for s in props.settings])
                        for op, sep, parts, weight, props in collector.rows]
                found = nc._search_entries(sample['query'], set())
                mx, my = area.x + area.width // 3, area.y + int(area.height * 0.8)
                record = dict(sample, index=state['index'], context=key, mouse=[mx, my],
                              window=[window.width, window.height],
                              plugin=[e.identifier for e in found],
                              screenshot=f'{state["index"]:03d}.png')
                report['samples'].append(record)
            window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=mx, y=my)
            state['phase'] = 'open'
            return 0.25
        if state['phase'] == 'open':
            with bpy.context.temp_override(window=window, area=state['area'], region=state['region']):
                bpy.ops.wm.search_single_menu('INVOKE_DEFAULT', menu_idname='NODE_MT_add', initial_query=sample['query'])
            state['phase'] = 'capture'
            return 0.65
        if state['phase'] == 'capture':
            with bpy.context.temp_override(window=window):
                bpy.ops.screen.screenshot(filepath=str(OUTPUT / report['samples'][-1]['screenshot']), check_existing=False)
            window.event_simulate(type='ESC', value='PRESS')
            window.event_simulate(type='ESC', value='RELEASE')
            print('AUDIT_CAPTURE', state['index'], sample['tree'], sample['query'], flush=True)
            state['phase'] = 'setup'
            state['index'] += 1
            if state['index'] % 10 == 0:
                write_report()
            return 0.2
    except Exception:
        report['errors'].append(traceback.format_exc())
        write_report()
        print(report['errors'][-1], flush=True)
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(tick, first_interval=2)
