"""Exercise the real GPU popup with synthetic IME events in an isolated UI.

Measures bridge enqueue to draw-callback completion, not physical keyboard,
system candidate latency or display presentation. Never saves user preferences.
"""
import importlib.util
import cProfile
import io
import json
import os
from pathlib import Path
import sys
import pstats
import time
import traceback

import bpy

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
spec = importlib.util.spec_from_file_location('NCInputPreview', ROOT / '__init__.py',
                                            submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
adapter = importlib.import_module(nc.__name__ + '.ime_input.adapter')
Composition = importlib.import_module(nc.__name__ + '.ime_input.session').Composition
nc._settings_path = lambda: OUTPUT / 'settings.json'
nc._preferences = lambda: None


class Input(Composition):
    def drain(self, query):
        if state['pending'] and 'drain_wait_ms' not in state['pending']:
            state['pending']['drain_wait_ms'] = (time.perf_counter() - state['pending']['start']) * 1000
        return super().drain(query)

    def sync(self, query):
        pass

    def caret(self, *rect):
        pass

    def reacquire(self):
        return True


state = {'phase': 'open', 'cycle': 0, 'step': 0, 'pending': None}
report = {'version': bpy.app.version_string, 'samples': [], 'errors': []}
draw = nc.ENS_AddNodeByEnglishSearch._draw_callback
refresh = nc.ENS_AddNodeByEnglishSearch._refresh_query_results


def observed_refresh(self):
    start = time.perf_counter()
    refresh(self)
    if state['pending']:
        state['pending']['search_ms'] = (time.perf_counter() - start) * 1000


def observed_draw(self, context):
    start = time.perf_counter()
    if '--profile-draw' in sys.argv and state['pending'] and state['cycle'] == state['step'] == 0:
        profiler = cProfile.Profile()
        profiler.runcall(draw, self, context)
        stream = io.StringIO()
        pstats.Stats(profiler, stream=stream).sort_stats('cumtime').print_stats(30)
        report['draw_profile'] = stream.getvalue()
    else:
        draw(self, context)
    pending = state['pending']
    if pending and (self._query, self._ime_preedit) == pending['expected']:
        pending['draw_ms'] = (time.perf_counter() - start) * 1000
        pending['elapsed_ms'] = (time.perf_counter() - pending.pop('start')) * 1000
        pending['results'] = len(self._results)
        pending['first'] = self._results[0].english if self._results else None
        report['samples'].append(pending)
        state['pending'] = None


nc.ENS_AddNodeByEnglishSearch._draw_callback = observed_draw
nc.ENS_AddNodeByEnglishSearch._refresh_query_results = observed_refresh
nc.IME_UNINSTALL = adapter.install(nc, None, lambda *args, **kwargs: None, session_factory=Input)
warm = nc._warm_search_font


def observed_warm():
    start = time.perf_counter()
    result = warm()
    report['font_warm_ms'] = (time.perf_counter() - start) * 1000
    return result


nc._warm_search_font = observed_warm
nc.register()
area = max(bpy.context.screen.areas, key=lambda area: area.width * area.height)
area.type = 'NODE_EDITOR'
area.ui_type = 'GeometryNodeTree'
tree = bpy.data.node_groups.new('Isolated input preview', 'GeometryNodeTree')
area.spaces.active.pin = True
area.spaces.active.node_tree = tree
steps = [(2, 'she zhi', ('', 'she zhi')), (4, '\u8bbe\u7f6e', ('\u8bbe\u7f6e', '')),
         (2, 'xin', ('\u8bbe\u7f6e', 'xin')), (2, '', ('\u8bbe\u7f6e', '')),
         (4, '', ('', ''))]


def tick():
    try:
        window = bpy.context.window_manager.windows[0]
        region = next(region for region in area.regions if region.type == 'WINDOW')
        with bpy.context.temp_override(window=window, area=area, region=region):
            if state['phase'] == 'open':
                if state['cycle'] == 3:
                    assert len(report['samples']) == 15
                    assert all(sample['results'] for sample in report['samples']
                               if sample['step'] in (0, 1, 3))
                    (OUTPUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
                    print('INPUT_PREVIEW_OK', [round(s['elapsed_ms'], 2) for s in report['samples']], flush=True)
                    nc.unregister()
                    bpy.ops.wm.quit_blender()
                    return None
                window.event_simulate(type='MOUSEMOVE', value='NOTHING',
                                      x=area.x + area.width // 2, y=area.y + area.height // 2)
                state['phase'] = 'invoke'
                return 0.1
            if state['phase'] == 'invoke':
                bpy.ops.node.node_console('INVOKE_DEFAULT')
                assert nc.ACTIVE_CONSOLE_OPERATOR is not None
                state['phase'] = 'send'
                return 0.1
            if state['phase'] == 'send':
                if state['step'] == len(steps):
                    nc.ACTIVE_CONSOLE_OPERATOR._finish(bpy.context, {'CANCELLED'})
                    state.update(cycle=state['cycle'] + 1, step=0, phase='open')
                    return 0.1
                kind, text, expected = steps[state['step']]
                state['pending'] = dict(cycle=state['cycle'], step=state['step'],
                                        expected=expected, start=time.perf_counter())
                nc.ACTIVE_CONSOLE_OPERATOR._ime_session.receive(kind, text)
                state['phase'] = 'wait'
                return 0.03
            if state['pending']:
                assert time.perf_counter() - state['pending']['start'] < 3, 'Input did not redraw'
                return 0.03
            if state['cycle'] == 0 and state['step'] in (0, 1):
                bpy.ops.screen.screenshot(filepath=str(OUTPUT / f"preview-{state['step']}.png"), check_existing=False)
            state['step'] += 1
            state['phase'] = 'send'
            return 0.05
    except Exception:
        report['errors'].append(traceback.format_exc())
        (OUTPUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(report['errors'][-1], flush=True)
        nc.unregister()
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(tick, first_interval=2)
