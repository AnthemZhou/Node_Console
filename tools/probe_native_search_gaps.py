"""Verify RNA/menu facts behind audit differences in an isolated Blender."""
import json
import os
from pathlib import Path
import sys

import bpy


assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
output = Path(sys.argv[sys.argv.index('--') + 1])
report = dict(version=bpy.app.version_string, build=bpy.app.build_hash.decode(), nodes=[])
menu = bpy.types.NODE_MT_category_shader_output
report['output_menu'] = dict(
    draw_module=menu.draw.__module__,
    functions=[f'{f.__module__}.{f.__qualname__}' for f in getattr(menu.draw, '_draw_funcs', [menu.draw])],
)
tree = bpy.data.node_groups.new('Isolated RNA probe', 'ShaderNodeTree')
try:
    for identifier in ['ShaderNodeBsdfGlossy', 'ShaderNodeBsdfAnisotropic']:
        node = tree.nodes.new(identifier)
        report['nodes'].append(dict(requested=identifier, actual=node.bl_idname, label=node.bl_label))
    node = tree.nodes.new('ShaderNodeMapRange')
    default = node.data_type
    node.data_type = 'FLOAT_VECTOR'
    report['map_range'] = dict(identifier=node.bl_idname, default=default, vector_variant=node.data_type)
    assert default == 'FLOAT' and node.data_type == 'FLOAT_VECTOR'
    node = tree.nodes.new('ShaderNodeMix')
    node.data_type = 'RGBA'
    report['mix_color'] = dict(identifier=node.bl_idname, data_type=node.data_type, blend_type=node.blend_type)
    assert node.blend_type == 'MIX'
    report['typed_bundle_operator'] = bpy.ops.node.add_typed_bundle.get_rna_type().identifier
finally:
    bpy.data.node_groups.remove(tree)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
