"""Run in factory Blender with BLENDER_USER_SCRIPTS/CONFIG set to temp directories."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import addon_utils
import bpy

assert os.environ.get('BLENDER_USER_SCRIPTS', '').startswith('/private/tmp/')
archive = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
bpy.ops.preferences.addon_install(filepath=str(archive), overwrite=True)
module = addon_utils.enable('Node_Console', default_set=True)
assert module and module.ADDON_VERSION == '1.1.3'
assert str(Path(module.__file__)).startswith(os.environ['BLENDER_USER_SCRIPTS'])
for tree_type in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
    tree = bpy.data.node_groups.new('Package smoke test', tree_type)
    context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_type))
    module._rebuild_search_entries(context)
    assert module.NODE_SEARCH_ENTRIES
    bpy.data.node_groups.remove(tree)
addon_utils.disable('Node_Console', default_set=True)
assert addon_utils.enable('Node_Console', default_set=True)
addon_utils.disable('Node_Console', default_set=True)
print('PACKAGE_INSTALL_OK', bpy.app.version_string, archive.name)
