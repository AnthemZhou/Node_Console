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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_local_release import RUNTIME_FILES


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
        names = RUNTIME_FILES
        for name in names:
            (target / name).parent.mkdir(parents=True, exist_ok=True)
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
        prefs = SimpleNamespace(accept_beta_updates=False, update_release="NONE")
        nc._preferences = lambda: None
        nc.register()
        nc._preferences = lambda: prefs
        try:
            assert bpy.ops.node_console.update_addon.get_rna_type()
            assert "filepath" in bpy.ops.wm.path_open.get_rna_type().properties
            passed.append("updater operator registered and backup-folder control supported")
            assert nc.ENS_AddonPreferences.bl_rna.properties["accept_beta_updates"].default is False
            assert bpy.ops.node_console.install_release.get_rna_type()
            assert not bpy.ops.node_console.install_release.poll()
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
            job = SimpleNamespace(directory=root, poll=Mock(return_value={"state": "checking"}), close=Mock(),
                                  current_version=current_version, release=None)
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

            def release(version, beta=False):
                return {"tag": "v" + version, "version": version, "prerelease": beta}

            stable = release(current_version)
            newer = release(next_version)
            beta = release(next_version + "-beta.1", True)
            nc.UPDATE_JOB = job
            job.poll.return_value = {"state": "releases", "releases": [beta, newer, stable]}
            with patch.object(nc, "bpy", wrapper), patch.object(nc.addon_updater, "install_release") as replace:
                assert nc._poll_addon_update() is None
                replace.assert_not_called()
            assert nc.UPDATE_STATUS["state"] == "available"
            assert [item["tag"] for item in nc.UPDATE_RELEASES] == [newer["tag"], stable["tag"]]
            assert prefs.update_release == newer["tag"]
            assert (target / "__init__.py").read_bytes() == (ROOT / "__init__.py").read_bytes()
            passed.append("check only lists versions; beta hidden by default; no files installed")

            old = release("1.4.0")
            nc._set_update_releases([old])
            assert prefs.update_release == "NONE" and nc._selected_update_release() is None
            assert not bpy.ops.node_console.install_release.poll()
            items = nc._update_release_items(prefs, None)
            assert current_version in items[0][1] and items[0][0] == "NONE"
            assert nc._ui_text("Older Stable") in items[1][1]
            nc._set_update_releases([old, release("1.3.4"), release("1.3.3")])
            assert len(nc._update_release_items(prefs, None)) == 4
            assert prefs.update_release == "NONE"
            nc._set_update_releases([old, stable])
            assert prefs.update_release == stable["tag"]
            assert not bpy.ops.node_console.install_release.poll()
            assert nc._ui_text("Installed") in nc._release_label(stable)
            assert "RC" in nc._release_label(release(next_version + "-rc.1", True))
            nc._set_update_releases([old, stable, newer, release("1.3.4"), release("1.3.3")])
            assert len(nc.UPDATE_RELEASES) == 3
            assert prefs.update_release == newer["tag"]
            passed.append("latest three choices, current/old/RC labels, and stale results never default to downgrade")

            fields = {key: value for key, value in nc.NODECONSOLE_OT_InstallRelease.__dict__.items()
                      if not key.startswith("__")}
            Install = type("InstallHarness", (), fields)
            confirm = SimpleNamespace(window_manager=SimpleNamespace(invoke_props_dialog=Mock(return_value={"RUNNING_MODAL"})))
            operator = Install()
            operator.report = Mock()
            with patch.object(nc.addon_updater, "UpdateJob") as start:
                assert operator.execute(confirm) == {"CANCELLED"}
                assert operator.invoke(confirm, None) == {"RUNNING_MODAL"}
                start.assert_not_called()
            # Closing the dialog here never runs execute and therefore never starts a job.
            assert nc.UPDATE_JOB is None
            prefs.update_release = stable["tag"]
            with patch.object(nc.addon_updater, "UpdateJob") as start:
                assert operator.execute(confirm) == {"CANCELLED"}
                start.assert_not_called()
            assert not bpy.ops.node_console.install_release.poll()
            passed.append("confirmation is required; cancel, changed selection and current version cannot install")

            prefs.accept_beta_updates = True
            with patch.object(nc, "_save_preference_settings") as save:
                nc._beta_updates_changed(prefs, None)
                save.assert_called_once()
            assert prefs.update_release == "NONE" and not nc.UPDATE_RELEASES
            nc._set_update_releases([beta, newer, stable])
            assert nc._selected_update_release() == newer
            prefs.update_release = beta["tag"]
            assert nc._selected_update_release() == beta
            beta_op = Install()
            beta_op.report = Mock()
            assert beta_op.invoke(confirm, None) == {"RUNNING_MODAL"}
            with patch.object(nc, "bpy", wrapper), patch.object(nc.addon_updater, "UpdateJob", return_value=job) as start:
                assert beta_op.execute(confirm) == {"FINISHED"}
                assert start.call_args.kwargs["allow_beta"] is True
                assert start.call_args.kwargs["release"] == beta
            prefs.accept_beta_updates = False
            with patch.object(nc, "_save_preference_settings"):
                nc._beta_updates_changed(prefs, None)
            assert nc.UPDATE_JOB is None and not nc.UPDATE_RELEASES
            assert not bpy.app.timers.is_registered(nc._poll_addon_update)
            passed.append("beta opt-in is explicit; toggling clears choices and cancels pending downloads without downgrade")

            nc._set_update_releases([newer, stable])
            install_op = Install()
            install_op.report = Mock()
            assert install_op.invoke(confirm, None) == {"RUNNING_MODAL"}
            job.release = dict(newer)
            with patch.object(nc, "bpy", wrapper), patch.object(nc.addon_updater, "UpdateJob", return_value=job) as start:
                assert install_op.execute(confirm) == {"FINISHED"}
                assert start.call_args.kwargs == {"action": "install", "allow_beta": False, "release": newer}

            with ZipFile(root / "release.zip", "w") as archive:
                for name in names:
                    content = (target / name).read_bytes()
                    if name == "__init__.py":
                        content = content.replace(f'ADDON_VERSION = "{current_version}"'.encode(), f'ADDON_VERSION = "{next_version}"'.encode())
                        content = content.replace(f'"version": {nc.bl_info["version"]}'.encode(), f'"version": {next_tuple}'.encode())
                    archive.writestr("Node_Console/" + name, content)
            job.poll.return_value = {"state": "ready", "version": next_version, "tag": newer["tag"]}
            nc.UPDATE_JOB = job
            with patch.object(nc, "bpy", wrapper), patch.object(nc.addon_reloader, "schedule") as schedule:
                nc.ACTIVE_CONSOLE_OPERATOR = object()
                assert nc._poll_addon_update() == 0.25
                assert nc.UPDATE_STATUS["state"] == "waiting"
                nc.ACTIVE_CONSOLE_OPERATOR = None
                assert nc._poll_addon_update() is None
                schedule.assert_called_once()
            assert nc.UPDATE_STATUS["state"] == "reloading", nc.UPDATE_STATUS
            assert not bpy.ops.node_console.update_addon.poll()
            assert f'ADDON_VERSION = "{next_version}"' in (target / "__init__.py").read_text()
            assert nc.ADDON_VERSION == current_version
            assert Path(nc.UPDATE_STATUS["backup"]).is_dir()
            assert settings.read_bytes() == saved_settings and snippets.read_bytes() == saved_snippets
            assert keymaps() == baseline_maps
            passed.append("staged replacement schedules deferred activation; current callback, keymaps and user data unchanged")

            nc.UPDATE_STATUS = {"state": "error", "code": "incompatible_blender"}
            original_language = bpy.context.preferences.view.language
            for language in ("en_US", "zh_HANS"):
                bpy.context.preferences.view.language = language
                assert nc._update_status_text()
            bpy.context.preferences.view.language = original_language
            passed.append("English and Chinese update status labels")
        finally:
            nc._preferences = lambda: None
            nc.unregister()
        assert nc.UPDATE_JOB is None and not bpy.app.timers.is_registered(nc._poll_addon_update)
        passed.append("unregister cleans up only its update task")
    report = {"version": bpy.app.version_string, "passed": passed}
    if "--" in sys.argv:
        Path(sys.argv[sys.argv.index("--") + 1]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
