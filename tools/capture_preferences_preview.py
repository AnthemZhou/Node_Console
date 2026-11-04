"""Render real Preferences in an isolated UI, without opening any web page."""
import os
from pathlib import Path
import shutil
import sys
import traceback

import addon_utils
import bpy
import gpu

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_local_release import RUNTIME_FILES

OUTPUT = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
scripts = Path(os.environ['BLENDER_USER_SCRIPTS']).resolve()
assert scripts.parent == Path(os.environ['BLENDER_USER_CONFIG']).resolve().parent
assert scripts.parent.name.startswith('node-console-isolated-')
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
english = '--english' in sys.argv
bpy.context.preferences.view.language = 'en_US' if english else 'zh_HANS'
target = scripts / 'addons' / 'Node_Console'
for name in RUNTIME_FILES:
    destination = target / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, destination)
bpy.utils.refresh_script_paths()
addon_utils.modules(refresh=True)
nc = addon_utils.enable('Node_Console', default_set=True)
assert nc and nc.__addon_enabled__
prefs = bpy.context.preferences.addons['Node_Console'].preferences
assert 'feedback_text' not in prefs.bl_rna.properties
addon_utils.module_bl_info(addon_utils.addons_fake_modules['Node_Console'])['show_expanded'] = True
nc._snippet_search_snapshot = lambda: {'snippets': [
    {'id': 'preview', 'tree_type': 'GeometryNodeTree', 'category': 'NONE',
     'name': 'Random Selection' if english else '\u968f\u673a\u8282\u70b9\u9009\u62e9', 'node_count': 3, 'link_count': 0}]}
prefs.snippet_nodes_expanded = True
area = max(bpy.context.screen.areas, key=lambda item: item.width * item.height)
area.type = 'PREFERENCES'
bpy.context.preferences.active_section = 'ADDONS'
bpy.context.window_manager.addon_search = 'Node Console'
step = 0
capture = None
captured = set()


def capture_frame():
    global capture
    if capture is None:
        return
    filename, capture = capture, None
    x, y, width, height = gpu.state.viewport_get()
    pixels = gpu.state.active_framebuffer_get().read_color(x, y, width, height, 4, 0, 'FLOAT')
    pixels.dimensions = width * height * 4
    preview = bpy.data.images.new('Preferences test framebuffer', width=width, height=height, alpha=True)
    try:
        preview.pixels.foreach_set(pixels)
        preview.filepath_raw = str(OUTPUT/filename)
        preview.file_format = 'PNG'
        preview.save()
        captured.add(filename)
    finally:
        bpy.data.images.remove(preview)


handler = bpy.types.SpacePreferences.draw_handler_add(capture_frame, (), 'WINDOW', 'POST_PIXEL')


def tick():
    global step, capture
    region = next(item for item in area.regions if item.type == 'WINDOW')
    with bpy.context.temp_override(area=area, region=region):
        if step == 0:
            capture = 'preferences-top.png'
        elif step == 1:
            assert 'preferences-top.png' in captured
            nc.UPDATE_STATUS = {'state': 'checking'}
            capture = 'preferences-checking.png'
        elif step < 5:
            assert 'preferences-checking.png' in captured
            bpy.ops.view2d.scroll_down(page=True)
        elif step == 5:
            capture = 'preferences-expanded.png'
        elif step == 6:
            assert 'preferences-expanded.png' in captured
            prefs.snippet_nodes_expanded = False
        elif step == 7:
            capture = 'preferences-collapsed.png'
        elif step == 8:
            assert 'preferences-collapsed.png' in captured
            bpy.types.SpacePreferences.draw_handler_remove(handler, 'WINDOW')
            addon_utils.disable('Node_Console', default_set=True)
            print('PREFERENCES_PREVIEW_OK', bpy.app.version_string, sorted(captured), flush=True)
            bpy.ops.wm.quit_blender()
            return None
        area.tag_redraw()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=2)
    step += 1
    return 0.5


def guarded_tick():
    try:
        return tick()
    except Exception:
        traceback.print_exc()
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(guarded_tick, first_interval=2)
