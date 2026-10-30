"""Exercise the release-browser command through a real Blender RNA dropdown."""
import importlib.util
import inspect
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bpy


def main():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('NCReleaseSelectionTest', root / '__init__.py',
                                                submodule_search_locations=[str(root)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    annotations = inspect.get_annotations(nc.ENS_AddonPreferences, eval_str=True)

    class ReleaseProbe(bpy.types.PropertyGroup):
        update_release: annotations['update_release']
        accept_beta_updates: bpy.props.BoolProperty(default=False)

    bpy.utils.register_class(ReleaseProbe)
    bpy.types.WindowManager.nc_release_probe = bpy.props.PointerProperty(type=ReleaseProbe)
    try:
        prefs = bpy.context.window_manager.nc_release_probe
        nc._preferences = lambda: prefs
        open_url = Mock()
        wrapper = SimpleNamespace(context=bpy.context, ops=SimpleNamespace(wm=SimpleNamespace(url_open=open_url)))
        with patch.object(nc, 'bpy', wrapper), patch.object(nc.addon_updater, 'UpdateJob') as download:
            for allow_beta in (False, True):
                prefs.accept_beta_updates = allow_beta
                releases = [dict(tag='v' + v, version=v, prerelease='-' in v)
                            for v in (nc.ADDON_VERSION, '1.4.1', '1.4.0', '1.3.4')]
                for available in ([], releases):
                    nc._set_update_releases(available)
                    items = nc._update_release_items(prefs, None)
                    assert items[-1][0] == nc.OTHER_RELEASES and len(items) <= 4
                    assert sum(item[0] != nc.OTHER_RELEASES for item in items) <= 3
                    for choice in items[:-1]:
                        prefs.update_release = choice[0]
                        selected = nc._selected_update_release()
                        open_url.reset_mock()
                        prefs.update_release = nc.OTHER_RELEASES
                        assert prefs.update_release == choice[0]
                        assert nc._selected_update_release() == selected
                        open_url.assert_called_once_with(url=nc.RELEASES_PAGE_URL)
                    open_url.reset_mock()
                    with patch.object(nc, 'PREFERENCES_LOADING', True):
                        prefs.update_release = nc.OTHER_RELEASES
                    open_url.assert_not_called()
                download.assert_not_called()
                assert nc.UPDATE_JOB is None
        print('RELEASE_SELECTION_REGRESSION', bpy.app.version_string, 'passed', flush=True)
    finally:
        del bpy.types.WindowManager.nc_release_probe
        bpy.utils.unregister_class(ReleaseProbe)


if __name__ == '__main__':
    main()
