"""Upgrade a release ZIP to a new build with the OLD updater/reloader on macOS."""
import ast
import ctypes
import os
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

import addon_utils
import bpy


assert os.environ.get("BLENDER_USER_CONFIG", "").startswith("/private/tmp/")
old_zip, new_zip = map(Path, sys.argv[sys.argv.index("--") + 1:])


def version(path):
    with ZipFile(path) as archive:
        source = archive.read("Node_Console/__init__.py").decode("utf-8")
    return next(ast.literal_eval(node.value) for node in ast.parse(source).body
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ADDON_VERSION"
                                                       for t in node.targets))


old_version, new_version = version(old_zip), version(new_zip)
with tempfile.TemporaryDirectory(prefix="nc-ime-upgrade-", dir="/private/tmp") as directory:
    root = Path(directory)
    with ZipFile(old_zip) as archive:
        archive.extractall(root)
    sys.path.insert(0, str(root))
    old = addon_utils.enable("Node_Console", default_set=True, persistent=True)
    assert old.ADDON_VERSION == old_version
    original_settings = old._load_settings()
    original_settings.update(favorites=["kept"], usage={"kept": 42}, shortcuts=["kept"])
    old._write_settings(original_settings)
    old._snippets_path().write_text('{"snippets": [{"id": "keep-library"}]}')
    protected = {path: path.read_bytes() for path in (old._settings_path(), old._snippets_path())}
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
    other = keymap.keymap_items.new("node.nw_add_texture", "T", "PRESS", ctrl=True)
    other.active = False
    other_id = other.id
    tree = bpy.data.node_groups.new("Unsaved data", "GeometryNodeTree")
    node = tree.nodes.new("ShaderNodeMath")
    node.inputs[0].default_value = 3.25
    pointer = node.as_pointer()
    backup = old.addon_updater.install_release(new_zip, root / "Node_Console", new_version, bpy.app.version,
                                               protected_paths=protected, current_version=old_version)
    new = old.addon_reloader.activate("Node_Console", backup, new_version)
    assert new.ADDON_VERSION == new_version and new.UPDATE_STATUS["state"] == "updated"
    assert callable(new.IME_UNINSTALL)
    assert all(path.read_bytes() == data for path, data in protected.items())
    assert other.id == other_id and not other.active and other.type == "T" and other.ctrl
    assert node.as_pointer() == pointer and node.inputs[0].default_value == 3.25
    from Node_Console.ime_input.library import materialize
    receiver = ctypes.CDLL(str(materialize(cache=root / "native-cache")))
    assert receiver.nc_ime_focused() == 0
    addon_utils.disable("Node_Console", default_set=True)
    assert new.IME_UNINSTALL is None
    print("IME_UPGRADE_OK", bpy.app.version_string, old_version, "->", new_version,
          "user data and other keymaps preserved")
