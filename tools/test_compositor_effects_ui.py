"""5.3 effect stacks resolve edit_tree during UI refresh, not background setup."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

import bpy
import gpu

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
assert bpy.app.version >= (5, 3, 0)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
output.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('NCEffectsTest', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._preferences = lambda: None
nc._refresh_asset_index()
area = max(bpy.context.screen.areas, key=lambda area: area.width * area.height)
area.type = 'NODE_EDITOR'
space = area.spaces.active
space.tree_type = 'CompositorNodeTree'
space.node_tree_sub_type = 'SCENE'
space.pin = False
trees, effects = [], []
for index in range(2):
    tree = bpy.data.node_groups.new('Effect test ' + str(index), 'CompositorNodeTree')
    effect = bpy.context.scene.compositor_effects.new('NC effect ' + str(index))
    effect.node_group = tree
    trees.append(tree)
    effects.append(effect)
effects[0].is_active = True
state = {'phase': 0}
report = {'version': bpy.app.version_string, 'created': [], 'errors': []}


def capture_draw():
    phase = state['phase']
    if bpy.context.area != area or phase not in (2, 5) or state.get('captured') == phase:
        return
    x, y, width, height = gpu.state.viewport_get()
    pixels = gpu.state.active_framebuffer_get().read_color(x, y, width, height, 4, 0, 'FLOAT')
    pixels.dimensions = width * height * 4
    image = bpy.data.images.new('Effect framebuffer', width=width, height=height, alpha=True)
    try:
        image.pixels.foreach_set(pixels)
        image.filepath_raw = str(output / ('effect-framebuffer-' + str(phase) + '.png'))
        image.file_format = 'PNG'
        image.save()
    finally:
        bpy.data.images.remove(image)
    state['captured'] = phase


handle = bpy.types.SpaceNodeEditor.draw_handler_add(capture_draw, (), 'WINDOW', 'POST_PIXEL')


def tick():
    try:
        region = next(region for region in area.regions if region.type == 'WINDOW')
        with bpy.context.temp_override(area=area, region=region):
            phase = state['phase']
            if phase in (0, 3):
                index = phase // 3
                assert space.edit_tree == trees[index], (index, space.edit_tree)
                nc._rebuild_search_entries(bpy.context)
                for row, query in enumerate(('Get Vector Component', 'Comment', 'Bloom')):
                    entry = next(e for e in nc._search_entries(query, set()) if e.english == query)
                    node = (nc._add_asset_node if entry.kind == 'ASSET' else nc._add_builtin_node)(bpy.context, entry)
                    assert node.id_data == trees[index]
                    node.location = (row * 240, 0)
                    report['created'].append(node.bl_idname)
                action = next(e for e in nc.NODE_SEARCH_ENTRIES if e.node_type == 'node.add_typed_bundle')
                node = nc._add_menu_action(bpy.context, action)
                assert node.bl_idname == 'NodeCombineBundle' and node.id_data == trees[index]
                assert any(item.name == 'Type' for item in node.bundle_items)
                node.location = (720, 0)
                report['created'].append(node.bl_idname)
                area.tag_redraw()
            elif phase in (1, 4):
                assert all(node.dimensions.x > 0 for node in space.edit_tree.nodes)
                bpy.ops.node.view_all()
                area.tag_redraw()
            elif phase in (2, 5):
                assert state.get('captured') == phase, 'No framebuffer capture'
                bpy.ops.screen.screenshot(filepath=str(output / ('effect-' + str(phase) + '.png')), check_existing=False)
                if phase == 2:
                    effects[1].is_active = True
                    area.tag_redraw()
            else:
                assert len(report['created']) == 8
                (output / 'report.json').write_text(json.dumps(report, indent=2))
                print('EFFECTS_UI_OK', report, flush=True)
                bpy.types.SpaceNodeEditor.draw_handler_remove(handle, 'WINDOW')
                bpy.ops.wm.quit_blender()
                return None
            state['phase'] += 1
            return 0.5
    except Exception:
        report['errors'].append(traceback.format_exc())
        (output / 'report.json').write_text(json.dumps(report, indent=2))
        print(report['errors'][-1], flush=True)
        bpy.types.SpaceNodeEditor.draw_handler_remove(handle, 'WINDOW')
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(tick, first_interval=2)
