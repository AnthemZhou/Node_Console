"""Render real GPU popup states in a separate --factory-startup Blender process.

Run without --background, with --python-exit-code 1 --python this_file -- output_dir.
The process closes after rendering; it never installs the add-on or reads user settings.
"""
import importlib.util
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bpy
import gpu
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]


def render():
    spec = importlib.util.spec_from_file_location(
        'NCPreview', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    nc._preferences = lambda: None
    nc._category_color_mode = lambda: 'LINE'
    Console = type('PreviewConsole', (), {
        key: value for key, value in nc.ENS_AddNodeByEnglishSearch.__dict__.items()
        if not key.startswith('__')})
    entries = [
        nc.NodeSearchEntry('join', 'Geometry', 'Join Geometry', '\u5408\u5e76\u51e0\u4f55\u4f53',
                           'Join Geometry', '', 'NODE', node_type='GeometryNodeJoinGeometry'),
        nc.NodeSearchEntry('noise', 'Texture', 'Noise Texture', '\u566a\u6ce2\u7eb9\u7406',
                           'Noise Texture', '', 'NODE', node_type='ShaderNodeTexNoise'),
        nc.NodeSearchEntry('add', 'Converter', 'Math > Add', '\u8fd0\u7b97 > \u76f8\u52a0',
                           'Math > Add', '', 'NODE', node_type='ShaderNodeMath'),
    ]
    output = Path(sys.argv[sys.argv.index('--') + 1])
    output.mkdir(parents=True, exist_ok=True)
    context = SimpleNamespace(region=SimpleNamespace(width=1200, height=640),
                              area=SimpleNamespace(tag_redraw=Mock()), window=object(),
                              window_manager=SimpleNamespace(event_timer_remove=Mock()))
    offscreen = gpu.types.GPUOffScreen(1200, 640)
    try:
        for scale, width in ((1.0, 250), (1.0, 400), (2.0, 400)):
            nc._ui_scale = lambda: scale
            nc._console_width = lambda: width
            op = Console()
            op._query = ''
            op._results = entries.copy()
            op._favorites = {'noise'}
            op._owns_context = lambda ctx: True
            op._anchor_x, op._anchor_y = 640, 520
            op._reset_shortcut_drag()
            nc.ACTIVE_CONSOLE_OPERATOR = op
            for state in ('idle', 'pressed', 'drag', 'settled'):
                if state == 'pressed':
                    op._shortcut_press_identifier = 'join'
                    op._shortcut_press_time = 0.0
                elif state == 'drag':
                    op._shortcut_dragging = True
                    op._shortcut_grab_offset = op._row_height / 2
                    op._shortcut_drag_mouse = (op._panel_rect[0] + 30, op._rows_top - op._row_height * 1.8)
                    op._update_shortcut_drag()
                    op._shortcut_animation_time = 9.95
                    with patch.object(nc.time, 'monotonic', return_value=10.0):
                        op._step_shortcut_animation(context)
                elif state == 'settled':
                    op._reset_shortcut_drag()
                with offscreen.bind():
                    framebuffer = gpu.state.active_framebuffer_get()
                    framebuffer.clear(color=(0.09, 0.09, 0.09, 1.0))
                    gpu.state.blend_set('ALPHA')
                    with gpu.matrix.push_pop(), gpu.matrix.push_pop_projection():
                        gpu.matrix.load_matrix(Matrix.Identity(4))
                        gpu.matrix.load_projection_matrix(Matrix((
                            (2 / 1200, 0, 0, -1), (0, 2 / 640, 0, -1),
                            (0, 0, -1, 0), (0, 0, 0, 1))))
                        op._draw_callback(context)
                    pixels = framebuffer.read_color(0, 0, 1200, 640, 4, 0, 'FLOAT')
                    pixels.dimensions = 1200 * 640 * 4
                    image = bpy.data.images.new('Node Console GPU Preview', 1200, 640, alpha=True)
                    try:
                        image.colorspace_settings.name = 'Non-Color'
                        image.pixels.foreach_set(pixels)
                        image.filepath_raw = str(output / f'{width}-{scale}-{state}.png')
                        image.file_format = 'PNG'
                        image.save()
                    finally:
                        bpy.data.images.remove(image)
    finally:
        offscreen.free()
    print('SHORTCUT_GPU_PREVIEWS', bpy.app.version_string, output, flush=True)
    return nc, Console, entries


class NCPreviewTimerProbe(bpy.types.Operator):
    bl_idname = 'wm.nc_preview_timer_probe'
    bl_label = 'Node Console Isolated Timer Test'

    def invoke(self, context, event):
        self.console = Console()
        self.console._owns_context = lambda ctx: True
        self.console._shortcut_row_offsets = {'join': 52.0}
        self.console._results = entries.copy()
        self.console._start_shortcut_animation(context)
        nc.ACTIVE_CONSOLE_OPERATOR = self.console
        self.started = time.monotonic()
        self.phase = 'settle'
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'RUNNING_MODAL'}
        try:
            assert not hasattr(event, 'timer'), 'Recheck timer routing for this Blender API'
            op = self.console
            op.modal(context, event)
            now = time.monotonic()
            assert now - self.started < 5, 'Animation failed to stop'
            if self.phase == 'settle' and op._shortcut_animation_timer is None:
                assert not op._shortcut_row_offsets
                self.phase = 'scroll'
                self.started = now
                op._panel_rect = (0, 40, 400, 100)
                op._padding, op._rows_top, op._row_height, op._visible_limit = 8, 100, 26, 2
                op._results = [nc.replace(entries[0], identifier=str(i)) for i in range(18)]
                op._shortcut_press_identifier = '0'
                op._shortcut_drag_mouse = (100, 50)
                op._shortcut_dragging = True
                op._shortcut_next_scroll_time = now + 0.2
                op._start_shortcut_animation(context)
            elif self.phase == 'scroll':
                elapsed = now - self.started
                assert op._scroll_offset <= int(elapsed / 0.2)
                if elapsed > 0.72:
                    assert 1 <= op._scroll_offset <= 3
                    op._reset_shortcut_drag(context)
                    assert op._shortcut_animation_timer is None
                    print('NATIVE_SHORTCUT_TIMER_PASS', bpy.app.version_string, flush=True)
                    bpy.app.timers.register(lambda: bpy.ops.wm.quit_blender() and None, first_interval=0.1)
                    return {'FINISHED'}
        except Exception:
            import traceback
            traceback.print_exc()
            # This is a dedicated factory-startup test process, never a user's session.
            import os
            os._exit(1)
        return {'RUNNING_MODAL'}


if __name__ == '__main__':
    nc, Console, entries = render()
    bpy.utils.register_class(NCPreviewTimerProbe)
    bpy.ops.wm.nc_preview_timer_probe('INVOKE_DEFAULT')
