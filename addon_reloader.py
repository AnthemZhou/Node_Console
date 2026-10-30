"""Deferred, package-local Blender reload with recovery of the previous version."""
import importlib
from pathlib import Path
import sys
import traceback
from types import ModuleType

import addon_utils
import bpy


_pending = None


def is_busy(module):
    wm = bpy.context.window_manager
    if (getattr(module, 'ACTIVE_CONSOLE_OPERATOR', None) is not None
            or getattr(module, 'ACTIVE_SNIPPET_DIALOG', None) is not None
            or wm.is_interface_locked):
        return True
    own_ids = {cls.bl_rna.identifier for cls in module.classes if cls.is_registered}
    for window in wm.windows:
        for operator in window.modal_operators:
            name = operator.bl_rna.identifier
            if name in own_ids or name.startswith(('TRANSFORM_OT_', 'NODE_OT_translate_attach')):
                return True
    return False


def _modules(name):
    return {key: value for key, value in sys.modules.copy().items()
            if key == name or key.startswith(name + '.')}


def _remove_modules(name):
    for key in _modules(name):
        del sys.modules[key]
    importlib.invalidate_caches()


def _refresh_metadata(module):
    # Preferences draws with refresh=False, so removing this entry hides the add-on.
    metadata = ModuleType(module.__name__)
    metadata.bl_info = dict(module.bl_info)
    metadata.__file__ = module.__file__
    metadata.__time__ = Path(module.__file__).stat().st_mtime
    addon_utils.addons_fake_modules[module.__name__] = metadata


def _preferences(module):
    prefs = module._preferences()
    if not prefs:
        return {}
    return {prop.identifier: getattr(prefs, prop.identifier)
            for prop in prefs.bl_rna.properties
            if not prop.is_readonly and prop.identifier != 'update_release'
            and prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}}


def _restore_preferences(module, values):
    prefs = module._preferences()
    if not prefs:
        return
    module.PREFERENCES_LOADING = True
    try:
        if hasattr(prefs, 'update_release'):
            prefs.update_release = 'NONE'
        for name, value in values.items():
            if hasattr(prefs, name):
                setattr(prefs, name, value)
    finally:
        module.PREFERENCES_LOADING = False
    module.refresh_keymap()


def activate(name, backup, expected_version):
    """Called only after the invoking operator/timer has returned to Blender."""
    old = sys.modules[name]
    if is_busy(old):
        raise RuntimeError('Node Console still has an active operation')
    target = Path(old.__file__).resolve().parent
    backup = Path(backup).resolve()
    if (backup.name != 'previous' or backup.parent.parent != target.parent
            or not backup.parent.name.startswith('.node-console-update-')
            or not (backup / '__init__.py').is_file()):
        raise RuntimeError('Invalid Node Console recovery directory')
    old_modules = _modules(name)
    preferences = _preferences(old)
    persistent = getattr(old, '__addon_persistent__', False)
    protected = {path: path.read_bytes() for path in (old._settings_path(), old._snippets_path()) if path.is_file()}
    candidate = None
    errors = []
    try:
        addon_utils.disable(name, default_set=False, handle_error=errors.append)
        if errors:
            raise RuntimeError('Could not unregister Node Console') from errors[0]
        _remove_modules(name)
        # Import separately so partially registered classes remain reachable on failure.
        candidate = importlib.import_module(name)
        if candidate.ADDON_VERSION != expected_version:
            raise RuntimeError('Loaded version does not match the update')
        candidate.__time__ = (target / '__init__.py').stat().st_mtime
        candidate.__addon_enabled__ = False
        loaded = addon_utils.enable(name, default_set=False, persistent=persistent, handle_error=errors.append)
        if loaded is None or errors:
            raise RuntimeError('Could not register the updated Node Console') from (errors[0] if errors else None)
        _restore_preferences(loaded, preferences)
        loaded.UPDATE_STATUS = {'state': 'updated', 'version': expected_version, 'backup': str(backup)}
    except Exception:
        traceback.print_exc()
        if candidate is not None:
            try:
                candidate.unregister()
            except Exception:
                traceback.print_exc()
        _remove_modules(name)
        failed = backup.parent / 'failed'
        try:
            target.rename(failed)
            try:
                backup.rename(target)
            except Exception:
                failed.rename(target)
                raise
            for path, content in protected.items():
                if not path.exists() or path.read_bytes() != content:
                    path.write_bytes(content)
            sys.modules.update(old_modules)
            old.__time__ = (target / '__init__.py').stat().st_mtime
            old.__addon_enabled__ = False
            errors.clear()
            loaded = addon_utils.enable(name, default_set=False, persistent=persistent, handle_error=errors.append)
            if loaded is None or errors:
                raise RuntimeError('Could not restore the previous Node Console')
            _restore_preferences(loaded, preferences)
            loaded.UPDATE_STATUS = {'state': 'error', 'code': 'reload_rolled_back', 'backup': str(failed)}
        except Exception:
            traceback.print_exc()
            # Do not claim recovery when Blender could not register the old code.
            old.UPDATE_STATUS = {'state': 'error', 'code': 'reload_failed', 'backup': str(backup.parent)}
            raise
    _refresh_metadata(loaded)
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    return loaded


def schedule(name, backup, expected_version):
    global _pending
    if _pending is not None:
        raise RuntimeError('A Node Console reload is already scheduled')
    original = sys.modules[name]

    def reload_when_idle():
        global _pending
        if sys.modules.get(name) is not original or not getattr(original, '__addon_enabled__', False):
            _pending = None
            return None
        if is_busy(original):
            original.UPDATE_STATUS['state'] = 'waiting_reload'
            original._redraw_update_preferences()
            return 0.25
        _pending = None
        try:
            activate(name, backup, expected_version)
        except Exception:
            traceback.print_exc()
        return None

    _pending = reload_when_idle
    try:
        bpy.app.timers.register(reload_when_idle, first_interval=0.25, persistent=True)
    except Exception:
        _pending = None
        raise
    return reload_when_idle


def cancel():
    global _pending
    if _pending is not None:
        if bpy.app.timers.is_registered(_pending):
            bpy.app.timers.unregister(_pending)
        _pending = None
