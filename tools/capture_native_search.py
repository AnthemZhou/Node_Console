"""Capture the real Blender search popup in an isolated UI process.

Run using run_isolated_blender.py --ui. No add-on registration, preference save,
or scene save. Captures are local-only evidence, not release contents.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

import bpy

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(sys.argv[sys.argv.index('--')+1]).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.use_translate_interface = True
spec = importlib.util.spec_from_file_location('NCNativeCapture', ROOT/'__init__.py',
                                             submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._settings_path = lambda: OUTPUT/'test-settings.json'
nc._preferences = lambda: None
nc._refresh_asset_index()
queries = [
    ('GeometryNodeTree','en_US','mesh'), ('GeometryNodeTree','en_US','instance'),
    ('GeometryNodeTree','en_US','add'), ('GeometryNodeTree','en_US','line'),
    ('GeometryNodeTree','en_US','nt'), ('GeometryNodeTree','en_US','niose'),
    ('GeometryNodeTree','en_US','join'), ('GeometryNodeTree','en_US','position'),
    ('GeometryNodeTree','zh_HANS','集合'), ('GeometryNodeTree','zh_HANS','噪波'),
    ('GeometryNodeTree','zh_HANS','实例'), ('ShaderNodeTree','en_US','add'),
    ('ShaderNodeTree','en_US','noise'), ('CompositorNodeTree','en_US','blur'),
    ('CompositorNodeTree','zh_HANS','模糊'),
]
if '--set-query' in sys.argv:
    queries = [(tree, 'zh_HANS', '\u8bbe\u7f6e') for tree in
               ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree')]
report = {'version':bpy.app.version_string, 'build':bpy.app.build_hash.decode(), 'samples':[], 'errors':[]}
state = {'index':0, 'phase':'setup'}


def tick():
    try:
        window = bpy.context.window_manager.windows[0]
        if state['index'] >= len(queries):
            (OUTPUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
            print('NATIVE_CAPTURE_COMPLETE',len(report['samples']),flush=True)
            bpy.ops.wm.quit_blender()
            return None
        index = state['index']
        tree_id, language, query = queries[index]
        if state['phase'] == 'setup':
            area = max(window.screen.areas,key=lambda area:area.width*area.height)
            area.type = 'NODE_EDITOR'
            space = area.spaces.active
            space.tree_type = tree_id
            space.pin = True
            tree = bpy.data.node_groups.new('Search validation '+str(index),tree_id)
            space.node_tree = tree
            if tree_id == 'ShaderNodeTree':
                space.shader_type = 'OBJECT'
            region = next(region for region in area.regions if region.type=='WINDOW')
            state.update(area=area,region=region,tree=tree)
            bpy.context.preferences.view.language = language
            with bpy.context.temp_override(window=window,area=area,region=region):
                nc._rebuild_search_entries(bpy.context)
                entries = nc._search_entries(query,set())
                report['samples'].append({'index':index,'tree':tree_id,'language':language,'query':query,
                    'plugin':[{'id':entry.identifier,'node':entry.node_type,'english':entry.english,
                               'settings':entry.settings,'paths':entry.menu_paths} for entry in entries[:10]]})
            window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=area.x+area.width//2,y=area.y+area.height//2)
            state['phase']='open'
            return 0.5
        if state['phase']=='open':
            with bpy.context.temp_override(window=window,area=state['area'],region=state['region']):
                bpy.ops.wm.search_single_menu('INVOKE_DEFAULT',menu_idname='NODE_MT_add',initial_query=query)
            state['phase']='capture'
            return 1.0
        if state['phase']=='capture':
            with bpy.context.temp_override(window=window):
                bpy.ops.screen.screenshot(filepath=str(OUTPUT/f'{index:02d}.png'),check_existing=False)
            window.event_simulate(type='ESC',value='PRESS')
            window.event_simulate(type='ESC',value='RELEASE')
            state['phase']='cleanup'
            return 0.5
        bpy.data.node_groups.remove(state['tree'])
        state['index']+=1
        state['phase']='setup'
        return 0.3
    except Exception:
        report['errors'].append(traceback.format_exc())
        (OUTPUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(report['errors'][-1],flush=True)
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(tick, first_interval=1)
