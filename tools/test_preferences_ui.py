"""Update header layout regressions in a factory-startup Blender process."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import bpy


class Layout:
    def __init__(self, kind='root', parent=None, **props):
        self.kind, self.parent, self.props = kind, parent, props
        self.children = []
        self.enabled = True
        self.alert = False
        self.alignment = 'EXPAND'

    def add(self, kind, **props):
        item = Layout(kind, self, **props)
        self.children.append(item)
        return item

    def row(self, **props):
        return self.add('row', **props)

    def column(self, **props):
        return self.add('column', **props)

    def label(self, **props):
        return self.add('label', **props)

    def separator(self, **props):
        return self.add('separator', **props)

    def box(self, **props):
        return self.add('box', **props)

    def split(self, **props):
        return self.add('split', **props)

    def prop(self, obj, name, **props):
        return self.add('prop', name=name, **props)

    def operator(self, name, **props):
        return self.add('operator', name=name, **props)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


def main():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('NCPreferencesUITest', root / '__init__.py', submodule_search_locations=[str(root)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    cases = 0
    states = ({'state': 'idle'}, {'state': 'current'}, {'state': 'checking'},
              {'state': 'downloading', 'version': '1.3.1'}, {'state': 'waiting'},
              {'state': 'installed', 'version': '1.3.1', 'backup': '/tmp/previous'},
              {'state': 'updated', 'version': '1.3.1'}, {'state': 'reloading'},
              {'state': 'waiting_reload'}, {'state': 'error', 'code': 'reload_rolled_back'},
              {'state': 'error', 'code': 'offline'})
    states += ({'state': 'available'}, {'state': 'empty'})
    prefs = SimpleNamespace(accept_beta_updates=True, update_release='v' + nc.ADDON_VERSION)
    releases = [dict(tag='v' + nc.ADDON_VERSION, version=nc.ADDON_VERSION, prerelease='-' in nc.ADDON_VERSION)]
    for language in ('en_US', 'zh_HANS'):
        bpy.context.preferences.view.language = language
        for scale in (1.0, 1.5, 2.0):
            for width in (1200, 420):
                for state in states:
                    layout = Layout()
                    context = SimpleNamespace(region=SimpleNamespace(width=round(width * scale)))
                    with patch.object(nc, 'UPDATE_STATUS', state), \
                            patch.object(nc, '_preferences', return_value=prefs), \
                            patch.object(nc, 'UPDATE_RELEASES', releases), \
                            patch.object(nc, '_resolution_scale', return_value=scale):
                        nc._draw_update_header(layout, context)
                    buttons = [item for item in layout.walk() if item.kind == 'operator']
                    update = next(item for item in buttons if item.props['name'] == 'node_console.update_addon')
                    install = next(item for item in buttons if item.props['name'] == 'node_console.install_release')
                    assert update.props['icon'] == 'FILE_REFRESH' and update.props['text'] == nc._ui_text('Update')
                    assert update.parent.ui_units_x >= 4
                    assert install.props['icon'] == 'IMPORT' and install.props['text'] == ''
                    assert install.parent.operator_context == 'INVOKE_DEFAULT'
                    normal = state['state'] in {'idle', 'available', 'current', 'updated'}
                    if normal:
                        assert len(layout.children) == (1 if width == 1200 else 2), (language, scale, width, state)
                        labels = [item.props['text'] for item in layout.walk() if item.kind == 'label']
                        assert labels == [f'Node Console v{nc.ADDON_VERSION}']
                    props = [item for item in layout.walk() if item.kind == 'prop']
                    assert {item.props['name'] for item in props} == {'accept_beta_updates', 'update_release'}
                    beta = next(item for item in props if item.props['name'] == 'accept_beta_updates')
                    assert beta.props['text'] == 'Beta'
                    if layout.children[0].kind == 'split':
                        assert layout.children[0].props['factor'] == 0.5
                        assert beta.parent.children[0] is beta
                    for child in layout.children:
                        if child.kind == 'column':
                            assert child.alert == (state['state'] == 'error')
                            for line in child.children:
                                assert nc._text_width(line.props['text'], nc._scaled(13, scale)) <= max(120 * scale, (width - 160) * scale)
                    if state.get('backup'):
                        backup = next(item for item in buttons if item.props['name'] == 'wm.path_open')
                        assert backup.filepath == state['backup']
                    cases += 1
        with patch.object(nc, '_preferences', return_value=prefs), patch.object(nc, 'UPDATE_RELEASES', releases):
            items = nc._update_release_items(prefs, None)
            assert items is nc._update_release_items(prefs, None)
            assert nc._ui_text('Installed') in items[0][1]
            assert nc._selected_update_release() == releases[0]
            assert items[-1][0] == nc.OTHER_RELEASES
            assert items[-1][1] == nc._ui_text('Other Versions')
            for version, beta, label in [('1.4.0', False, nc._ui_text('Older Stable')),
                                         ('1.5.0-beta.1', True, 'Beta'), ('1.5.0-rc.1', True, 'RC')]:
                assert label in nc._release_label(dict(version=version, prerelease=beta))
        cases += 1
    prefs = SimpleNamespace(layout=Layout(), snippet_nodes_expanded=False)
    context = SimpleNamespace(region=SimpleNamespace(width=1200))
    with patch.object(nc, '_load_asset_index', return_value=[]), \
            patch.object(nc, '_load_favorite_meta', return_value={}), \
            patch.object(nc, '_load_identifier_tree_meta', return_value={}), \
            patch.object(nc, '_load_favorites', return_value=set()), \
            patch.object(nc, '_load_shortcuts', return_value=[]), \
            patch.object(nc, '_shortcut_conflict_labels', return_value=[]), \
            patch.object(nc, '_snippet_search_snapshot', return_value={'snippets': []}) as snippets:
        nc.ENS_AddonPreferences.draw(prefs, context)
        snippets.assert_not_called()
        settings_box = prefs.layout.children[0]
        assert settings_box.kind == 'box'
        splits = [item for item in settings_box.children if item.kind == 'split']
        assert splits[0].props['factor'] == splits[1].props['factor'] == 0.5
        prefs.snippet_nodes_expanded = True
        nc.ENS_AddonPreferences.draw(prefs, context)
        snippets.assert_called_once()
    cases += 1
    print('PREFERENCES_UI_REGRESSION', bpy.app.version_string, cases, 'passed', flush=True)


if __name__ == '__main__':
    main()
