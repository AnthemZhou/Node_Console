"""Real package downgrade and return, isolated from installed add-ons and prefs."""
import ast
import os
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

import addon_utils
import bpy


def package_version(path):
    with ZipFile(path) as archive:
        tree = ast.parse(archive.read("Node_Console/__init__.py"))
    return next(ast.literal_eval(item.value) for item in tree.body if isinstance(item, ast.Assign)
                and any(isinstance(name, ast.Name) and name.id == "ADDON_VERSION" for name in item.targets))


assert os.environ.get("BLENDER_USER_CONFIG", "").startswith("/private/tmp/")
current_zip, previous_zip = map(Path, sys.argv[sys.argv.index("--") + 1:])
current_version, previous_version = map(package_version, (current_zip, previous_zip))
with tempfile.TemporaryDirectory(prefix="nc-release-switch-", dir="/private/tmp") as directory:
    root = Path(directory)
    with ZipFile(current_zip) as archive:
        archive.extractall(root)
    sys.path.insert(0, str(root))
    current = addon_utils.enable("Node_Console", default_set=True, persistent=True)
    assert current.ADDON_VERSION == current_version
    prefs = current._preferences()
    assert not prefs.accept_beta_updates
    prefs.accept_beta_updates = True
    current._set_update_releases([
        dict(version=current_version, tag="v" + current_version, prerelease=False),
        dict(version=previous_version, tag="v" + previous_version, prerelease=False)])
    prefs.update_release = "v" + previous_version
    assert current._selected_update_release()["version"] == previous_version
    assert "update_release" not in current.addon_reloader._preferences(current)
    data = current._load_settings()
    data.update(favorites=["preserve"], usage={"preserve": 5}, shortcuts=["preserve"])
    current._write_settings(data)
    current._snippets_path().write_text('{"snippets":[{"id":"preserve"}]}')
    protected = {path: path.read_bytes() for path in (current._settings_path(), current._snippets_path())}
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
    other = keymap.keymap_items.new("node.nw_add_texture", "T", "PRESS", ctrl=True)
    other.active = False
    other_id = other.id
    tree = bpy.data.node_groups.new("Unsaved release switch test", "GeometryNodeTree")
    node = tree.nodes.new("ShaderNodeMath")
    node.inputs[0].default_value = 3.25
    pointer = node.as_pointer()
    for archive, target_version, downgrade in ((previous_zip, previous_version, True),
                                                (current_zip, current_version, False)):
        options = {"allow_downgrade": True} if downgrade else {}
        backup = current.addon_updater.install_release(archive, root / "Node_Console", target_version,
                     bpy.app.version, protected_paths=protected, current_version=current.ADDON_VERSION, **options)
        current = current.addon_reloader.activate("Node_Console", backup, target_version)
        assert current.ADDON_VERSION == target_version and current.UPDATE_STATUS["state"] == "updated"
        assert all(path.read_bytes() == content for path, content in protected.items())
        assert other.id == other_id and not other.active and other.ctrl and other.type == "T"
        assert node.as_pointer() == pointer and node.inputs[0].default_value == 3.25
    assert current._preferences().accept_beta_updates
    assert current._preferences().update_release == "NONE"
    addon_utils.disable("Node_Console", default_set=True)
    print("RELEASE_SWITCH_OK", bpy.app.version_string, current_version, "->", previous_version,
          "->", current_version, "data/preferences/keymaps/unsaved nodes preserved; transient selector reset")
