"""Render real Preferences in an isolated UI, without opening any web page."""
import os
from pathlib import Path
import sys
import traceback

import addon_utils
import bpy
import gpu

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.language = 'zh_HANS'
bpy.ops.preferences.addon_install(filepath=str(ROOT/'Node_Console_1.5.0.zip'), overwrite=True)
nc = addon_utils.enable('Node_Console', default_set=True)
prefs = bpy.context.preferences.addons['Node_Console'].preferences
addon_utils.modules(refresh=True)
addon_utils.module_bl_info(addon_utils.addons_fake_modules['Node_Console'])['show_expanded'] = True
seen = set()
draw_feedback = nc._draw_feedback


def observed_feedback(layout, prefs):
    draw_feedback(layout, prefs)
    seen.add(bool(prefs.feedback_text))


nc._draw_feedback = observed_feedback
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
    preview = bpy.data.images.new('Feedback test framebuffer', width=width, height=height, alpha=True)
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
        if step < 3:
            bpy.ops.view2d.scroll_down(page=True)
        elif step == 3:
            assert False in seen, 'Empty feedback field did not draw'
            bpy.ops.screen.screenshot(filepath=str(OUTPUT/'feedback-empty.png'), check_existing=False)
            prefs.feedback_text = '切换组合点模式后搜索结果没有更新，请检查。'
            area.tag_redraw()
        elif step == 4:
            assert True in seen, 'Filled feedback field did not draw'
            capture = 'feedback-filled-framebuffer.png'
            area.tag_redraw()
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=2)
        elif step == 5:
            assert 'feedback-filled-framebuffer.png' in captured
            bpy.ops.screen.screenshot(filepath=str(OUTPUT/'feedback-filled.png'), check_existing=False)
            bpy.types.SpacePreferences.draw_handler_remove(handler, 'WINDOW')
            addon_utils.disable('Node_Console', default_set=True)
            print('FEEDBACK_PREVIEW_OK', bpy.app.version_string, flush=True)
            bpy.ops.wm.quit_blender()
            return None
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
