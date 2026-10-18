"""Real same-process updates/rollback, using only temporary installed packages/data."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zipfile import ZipFile

import addon_utils
import bpy


ROOT = Path(__file__).resolve().parents[1]
FILES = ('__init__.py', 'addon_reloader.py', 'addon_updater.py', 'node_registry.py',
         'node_search_aliases.json', 'node_console_builtin_cache.json')


def keymaps():
    return sorted((config.name, km.name, item.idname, item.type, item.value,
                   item.shift, item.ctrl, item.alt, item.oskey, item.active)
                  for config in bpy.context.window_manager.keyconfigs
                  for km in config.keymaps for item in km.keymap_items)


def package(directory, current, next_version, failure=None):
    archive = directory / 'release.zip'
    with ZipFile(archive, 'w') as output:
        for name in FILES:
            content = (ROOT / name).read_text(encoding='utf-8')
            if name == '__init__.py':
                source_version = next(line.split('"')[1] for line in content.splitlines()
                                      if line.startswith('ADDON_VERSION ='))
                content = content.replace(f'ADDON_VERSION = "{source_version}"', f'ADDON_VERSION = "{next_version}"')
                content = content.replace(f'"version": {tuple(map(int, source_version.split(".")))}',
                                          f'"version": {tuple(map(int, next_version.split(".")))}')
                if failure == 'register':
                    content += '\n_register_impl = register\ndef register():\n    _register_impl()\n    raise RuntimeError("intentional registration failure")\n'
                elif failure == 'import':
                    content += '\nraise RuntimeError("intentional import failure")\n'
            if name == 'node_registry.py':
                content += f'\nHOT_RELOAD_TEST_MARKER = "{next_version}"\n'
            output.writestr('Node_Console/' + name, content)
    return archive


def main():
    assert os.environ.get('BLENDER_USER_CONFIG', '').startswith('/private/tmp/')
    passed = []
    with tempfile.TemporaryDirectory(prefix='nc-hot-reload-', dir='/private/tmp') as directory:
        root = Path(directory)
        target = root / 'Node_Console'
        target.mkdir()
        for name in FILES:
            shutil.copy2(ROOT / name, target / name)
        sys.path.insert(0, str(root))
        nc = addon_utils.enable('Node_Console', default_set=True, persistent=True)
        assert nc and nc.__addon_enabled__
        addon_utils.modules()
        other_metadata = dict(addon_utils.addons_fake_modules)
        other_metadata.pop('Node_Console', None)
        try:
            prefs = nc._preferences()
            prefs.display_mode = 'CHINESE_ENGLISH'
            prefs.console_width = 333
            prefs.shortcut_alt = True
            prefs.snippet_shortcut_key = 'F'
            prefs.snippet_library_path = str(root / 'my-snippets.json')
            nc._snippets_path().write_text('{"snippets":[{"id":"personal"}]}')
            settings = nc._load_settings()
            settings.update(favorites=['kept'], usage={'kept': 99}, shortcuts=['kept'],
                            shortcut_order_by_tree={'ShaderNodeTree': ['kept']}, future_field={'value': 7})
            nc._write_settings(settings)
            nc.refresh_keymap()
            km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
            other = km.keymap_items.new('node.nw_add_texture', 'T', 'PRESS', ctrl=True)
            other.active = False
            bpy.context.window_manager.keyconfigs.update()
            initial_maps = keymaps()
            initial_prefs = nc.addon_reloader._preferences(nc)
            initial_files = {path: path.read_bytes() for path in (nc._settings_path(), nc._snippets_path())}
            tree = bpy.data.node_groups.new('Unsaved graph survives updates', 'GeometryNodeTree')
            node = tree.nodes.new('ShaderNodeMath')
            node.inputs[0].default_value = 7.5
            node_pointer = node.as_pointer()

            def assert_preserved(module):
                assert module.__addon_enabled__ and module.__addon_persistent__
                assert keymaps() == initial_maps, (set(keymaps()) - set(initial_maps), set(initial_maps) - set(keymaps()))
                assert module.addon_reloader._preferences(module) == initial_prefs
                for path, data in initial_files.items():
                    assert path.read_bytes() == data, path.name
                assert node.as_pointer() == node_pointer and node.inputs[0].default_value == 7.5
                assert 'Node_Console' in bpy.context.preferences.addons
                assert bpy.ops.node_console.save_snippet.get_rna_type()
                module._rebuild_search_entries(SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree.bl_idname)))
                assert module.NODE_SEARCH_ENTRIES
                # Searches may persist a versioned index; that becomes the next update's baseline.
                assert {key: value for key, value in module._load_settings().items() if key != 'search_index_cache'} == {
                    key: value for key, value in settings.items() if key != 'search_index_cache'}
                initial_files.update({path: path.read_bytes() for path in initial_files})

            for failure in (None, None, 'register', 'import'):
                old = nc
                version = '.'.join(map(str, (*nc.bl_info['version'][:2], nc.bl_info['version'][2] + 1)))
                package(root, nc.ADDON_VERSION, version, failure)
                old_callbacks = (nc._background_asset_index_step, nc._refresh_keymap_from_timer, nc._retry_register_keymap)
                for callback in old_callbacks:
                    if not bpy.app.timers.is_registered(callback):
                        bpy.app.timers.register(callback, first_interval=60)
                job = SimpleNamespace(directory=root, poll=Mock(return_value={'state': 'ready', 'version': version}), close=Mock())
                nc.UPDATE_JOB = job
                wrapper = SimpleNamespace(app=SimpleNamespace(online_access=True, version=bpy.app.version, timers=bpy.app.timers),
                                          context=bpy.context, path=bpy.path, utils=bpy.utils)
                with patch.object(nc, 'bpy', wrapper):
                    nc.ACTIVE_SNIPPET_DIALOG = object()
                    assert nc._poll_addon_update() == 0.25
                    assert nc.UPDATE_STATUS['state'] == 'waiting'
                    nc.ACTIVE_SNIPPET_DIALOG = None
                    assert nc._poll_addon_update() is None
                job.close.assert_called_once()
                callback = nc.addon_reloader._pending
                assert callback and bpy.app.timers.is_registered(callback)
                nc.ACTIVE_CONSOLE_OPERATOR = object()
                assert callback() == 0.25
                assert nc.UPDATE_STATUS['state'] == 'waiting_reload'
                nc.ACTIVE_CONSOLE_OPERATOR = None
                bpy.app.timers.unregister(callback)
                callback()
                nc = sys.modules['Node_Console']
                if failure:
                    assert nc is old and nc.UPDATE_STATUS['code'] == 'reload_rolled_back', nc.UPDATE_STATUS
                    assert nc.ADDON_VERSION != version
                else:
                    assert nc is not old and nc.ADDON_VERSION == version
                    assert nc.UPDATE_STATUS['state'] == 'updated'
                    assert nc.node_registry is not old.node_registry
                    assert nc.node_registry.HOT_RELOAD_TEST_MARKER == version
                    assert not any(cls.is_registered for cls in old.classes)
                assert not any(bpy.app.timers.is_registered(item) for item in old_callbacks)
                metadata = addon_utils.addons_fake_modules['Node_Console']
                assert metadata.bl_info['version'] == nc.bl_info['version']
                assert metadata.__file__ == nc.__file__
                assert metadata in addon_utils.modules(refresh=False)
                assert all(addon_utils.addons_fake_modules.get(name) is value
                           for name, value in other_metadata.items())
                assert_preserved(nc)
                passed.append(f'{failure or "success"}: fresh modules, preserved graph/preferences/data/keymaps, cleaned timers')

            next_version = '.'.join(map(str, (*nc.bl_info['version'][:2], nc.bl_info['version'][2] + 1)))
            package(root, nc.ADDON_VERSION, next_version)
            backup = nc.addon_updater.install_release(root / 'release.zip', target, next_version, bpy.app.version)
            callback = nc.addon_reloader.schedule('Node_Console', backup, next_version)
            addon_utils.disable('Node_Console', default_set=False)
            assert not bpy.app.timers.is_registered(callback)
            assert not nc.__addon_enabled__
            passed.append('manual disable cancels pending activation without re-enabling the add-on')
            nc = addon_utils.enable('Node_Console', default_set=False, persistent=True)
            assert nc.ADDON_VERSION == next_version
            assert nc.node_registry.HOT_RELOAD_TEST_MARKER == next_version
            assert_preserved(nc)
            passed.append('manual re-enable after cancelling activation also refreshes child modules')
        finally:
            if getattr(nc, '__addon_enabled__', False):
                addon_utils.disable('Node_Console', default_set=True)
            sys.path.remove(str(root))
    print('HOT_RELOAD_REGRESSION', bpy.app.version_string, json.dumps(passed, indent=2), flush=True)


if __name__ == '__main__':
    main()
