"""Register and exercise updater UI/controller in a factory-startup Blender."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zipfile import ZipFile

import bpy


ROOT = Path(__file__).resolve().parents[1]


def keymaps():
    return [(config.name, km.name, item.idname, item.type, item.value, item.shift, item.ctrl,
             item.alt, item.oskey, item.active)
            for config in bpy.context.window_manager.keyconfigs
            for km in config.keymaps for item in km.keymap_items]


def main():
    passed = []
    with tempfile.TemporaryDirectory(prefix="nc-blender-updater-") as directory:
        root = Path(directory)
        target = root / "Node_Console"
        target.mkdir()
        names = ("__init__.py", "addon_updater.py", "node_registry.py", "node_search_aliases.json", "node_console_builtin_cache.json")
        for name in names:
            shutil.copyfile(ROOT / name, target / name)
        spec = importlib.util.spec_from_file_location("NCUpdateTest", target / "__init__.py", submodule_search_locations=[str(target)])
        nc = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = nc
        spec.loader.exec_module(nc)
        current_version = nc.ADDON_VERSION
        next_tuple = (*nc.bl_info["version"][:2], nc.bl_info["version"][2] + 1)
        next_version = ".".join(map(str, next_tuple))
        settings, snippets = root / "settings.json", root / "snippets.json"
        settings.write_text(json.dumps({"settings_version": 2, "favorites": ["test"], "usage": {"test": 9},
                                        "shortcuts": ["test"], "shortcut_order_by_tree": {"ShaderNodeTree": ["test"]}}))
        snippets.write_text('{"snippets":[{"id":"personal"}]}')
        nc._settings_path = lambda: settings
        nc._snippets_path = lambda: snippets
        nc._preferences = lambda: None
        nc.register()
        try:
            assert bpy.ops.node_console.update_addon.get_rna_type()
            assert "filepath" in bpy.ops.wm.path_open.get_rna_type().properties
            passed.append("updater operator registered and backup-folder control supported")
            baseline_maps = keymaps()
            saved_settings, saved_snippets = settings.read_bytes(), snippets.read_bytes()
            app = SimpleNamespace(online_access=False, version=bpy.app.version, timers=bpy.app.timers)
            wrapper = SimpleNamespace(app=app, context=bpy.context)
            with patch.object(nc, "bpy", wrapper), patch.object(nc.addon_updater, "UpdateJob") as start:
                assert bpy.ops.node_console.update_addon() == {"CANCELLED"}
                start.assert_not_called()
                assert nc.UPDATE_STATUS["code"] == "offline"
                passed.append("offline permission blocks network access")

            app.online_access = True
            job = SimpleNamespace(directory=root, poll=Mock(return_value={"state": "checking"}), close=Mock())
            with patch.object(nc, "bpy", wrapper), patch.object(nc.addon_updater, "UpdateJob", return_value=job):
                assert bpy.ops.node_console.update_addon() == {"FINISHED"}
                assert not bpy.ops.node_console.update_addon.poll()
                assert nc._poll_addon_update() == 0.25
                nc._stop_addon_update()
                job.close.assert_called_once()
                assert not bpy.app.timers.is_registered(nc._poll_addon_update)
                passed.append("async launch, duplicate-click guard and cancellation cleanup")

            for result in ({"state": "current"}, {"state": "error", "code": "network_error"}):
                job.poll.return_value = result
                nc.UPDATE_JOB = job
                with patch.object(nc, "bpy", wrapper):
                    assert nc._poll_addon_update() is None
                assert nc.UPDATE_STATUS == result
            passed.append("up-to-date and network-error states leave files unchanged")

            with ZipFile(root / "release.zip", "w") as archive:
                for name in names:
                    content = (target / name).read_bytes()
                    if name == "__init__.py":
                        content = content.replace(f'ADDON_VERSION = "{current_version}"'.encode(), f'ADDON_VERSION = "{next_version}"'.encode())
                        content = content.replace(f'"version": {nc.bl_info["version"]}'.encode(), f'"version": {next_tuple}'.encode())
                    archive.writestr("Node_Console/" + name, content)
            job.poll.return_value = {"state": "ready", "version": next_version}
            nc.UPDATE_JOB = job
            with patch.object(nc, "bpy", wrapper):
                nc.ACTIVE_CONSOLE_OPERATOR = object()
                assert nc._poll_addon_update() == 0.25
                assert nc.UPDATE_STATUS["state"] == "waiting"
                nc.ACTIVE_CONSOLE_OPERATOR = None
                assert nc._poll_addon_update() is None
            assert nc.UPDATE_STATUS["state"] == "installed", nc.UPDATE_STATUS
            assert not bpy.ops.node_console.update_addon.poll()
            assert f'ADDON_VERSION = "{next_version}"' in (target / "__init__.py").read_text()
            assert nc.ADDON_VERSION == current_version
            assert Path(nc.UPDATE_STATUS["backup"]).is_dir()
            assert settings.read_bytes() == saved_settings and snippets.read_bytes() == saved_snippets
            assert keymaps() == baseline_maps
            passed.append("real staged replacement and backup; loaded code, keymaps, favorites, usage and snippets unchanged")

            nc.UPDATE_STATUS = {"state": "error", "code": "incompatible_blender"}
            original_language = bpy.context.preferences.view.language
            for language in ("en_US", "zh_HANS"):
                bpy.context.preferences.view.language = language
                assert nc._update_status_text()
            bpy.context.preferences.view.language = original_language
            passed.append("English and Chinese update status labels")
        finally:
            nc.unregister()
        assert nc.UPDATE_JOB is None and not bpy.app.timers.is_registered(nc._poll_addon_update)
        passed.append("unregister cleans up only its update task")
    report = {"version": bpy.app.version_string, "passed": passed}
    if "--" in sys.argv:
        Path(sys.argv[sys.argv.index("--") + 1]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
