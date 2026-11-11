"""Preferences layout regressions in a factory-startup Blender process."""
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
    for language in ('en_US', 'zh_HANS', 'ja_JP', 'ko_KR', 'ru_RU', 'es'):
        bpy.context.preferences.view.language = language
        for scale in (1.0, 1.5, 2.0):
            for width in (1200, 420):
                for state in states:
                    layout = Layout()
                    context = SimpleNamespace(region=SimpleNamespace(width=round(width * scale)),
                                              preferences=SimpleNamespace(system=SimpleNamespace(ui_scale=scale)))
                    with patch.object(nc, 'UPDATE_STATUS', state), \
                            patch.object(nc, '_preferences', return_value=prefs), \
                            patch.object(nc, 'UPDATE_RELEASES', releases), \
                            patch.object(nc, '_resolution_scale', return_value=1.0):
                        nc._draw_update_header(layout, context)
                        expected_status = nc._update_status_text()
                    buttons = [item for item in layout.walk() if item.kind == 'operator']
                    update = next(item for item in buttons if item.props['name'] == 'node_console.update_addon')
                    install = next(item for item in buttons if item.props['name'] == 'node_console.install_release')
                    update_label = bpy.app.translations.pgettext_iface(
                        nc._ui_text('Update'), bpy.app.translations.contexts.operator_default)
                    assert update.props['icon'] == 'FILE_REFRESH' and update.props['text'] == update_label
                    assert update.props['translate'] is False
                    assert update.parent.ui_units_x >= 4
                    assert install.props['icon'] == 'IMPORT' and install.props['text'] == ''
                    assert install.parent.operator_context == 'INVOKE_DEFAULT'
                    normal = state['state'] in {'idle', 'available', 'current', 'updated'}
                    assert len(layout.children) == (1 if width == 1200 else 2), (language, scale, width, state)
                    labels = [item for item in layout.walk() if item.kind == 'label']
                    assert labels[0].props['text'] == f'Node Console v{nc.ADDON_VERSION}'
                    assert labels[0].parent.alignment == 'LEFT'
                    assert not hasattr(labels[0].parent, 'ui_units_x')
                    assert labels[0].parent.parent.alignment == 'LEFT'
                    assert len(labels) == 2
                    assert labels[0].parent.parent is labels[1].parent.parent
                    assert labels[1].props['text'] == ('' if normal else expected_status)
                    assert labels[1].parent.alert == (state['state'] == 'error')
                    assert not any(item.kind == 'column' for item in layout.walk())
                    props = [item for item in layout.walk() if item.kind == 'prop']
                    assert {item.props['name'] for item in props} == {'accept_beta_updates', 'update_release'}
                    beta = next(item for item in props if item.props['name'] == 'accept_beta_updates')
                    assert beta.props['text'] == 'Beta'
                    assert beta.parent.alignment == 'LEFT'
                    if layout.children[0].kind == 'split':
                        assert layout.children[0].props['factor'] == 0.5
                        assert beta.parent.children[0] is beta
                    selector = next(item for item in props if item.props['name'] == 'update_release')
                    controls_width = (width - 48) * scale / (2 if width == 1200 else 1)
                    beta_split = beta.parent.parent
                    if width == 1200:
                        header = layout.children[0]
                        assert beta_split is header.children[0]
                        assert beta.parent is beta_split.children[1]
                        assert labels[0] in list(beta_split.children[0].walk())
                        assert selector in list(header.children[1].walk())
                        assert abs((1 - beta_split.props['factor']) * controls_width - 50 * scale) < 0.001
                        selector_space = controls_width
                    else:
                        assert beta_split is layout.children[1].children[0]
                        assert abs(beta_split.props['factor'] * controls_width - 50 * scale) < 0.001
                        selector_space = controls_width - 50 * scale
                    selector_width = selector.parent.parent.props['factor'] * selector_space
                    buttons_width = max(70 * scale, nc._text_width(update_label, round(13 * scale)) + 44 * scale)
                    assert abs(selector_width - (selector_space - buttons_width)) < 0.001
                    enabled = state['state'] not in {'installed', 'reloading', 'waiting_reload'}
                    assert beta.parent.enabled == selector.parent.enabled == enabled
                    assert [item.props['name'] for item in buttons] == [
                        'node_console.update_addon', 'node_console.install_release']
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
            for version, highlight in nc.addon_updater.RELEASE_HIGHLIGHTS.items():
                label = nc._release_label(dict(version=version, prerelease='-' in version))
                assert nc._ui_text(highlight) in label, (language, version, label)
                assert highlight in nc.UI_TEXT_ZH
            assert nc._ui_text(nc.addon_updater.RELEASE_HIGHLIGHTS[nc.ADDON_VERSION]) in items[0][1]
            assert items[0][1] in items[0][2]
            future = dict(version='1.5.0-beta.1', prerelease=True,
                          summary={'en': 'Faster startup', 'zh': '启动提速'})
            expected = future['summary']['zh' if language == 'zh_HANS' else 'en']
            assert expected in nc._release_label(future)
            assert 'Beta' in nc._release_label(future)
            with patch.object(nc, 'UPDATE_RELEASES', []):
                offline = nc._update_release_items(prefs, None)[0]
                assert offline[0] == 'NONE' and nc._ui_text('Installed') in offline[1]
                assert nc._ui_text(nc.addon_updater.RELEASE_HIGHLIGHTS[nc.ADDON_VERSION]) in offline[1]
                assert offline[1] in offline[2]
        cases += 1
    for language in ('en_US', 'zh_HANS'):
        bpy.context.preferences.view.language = language
        for points, zoom in ((11, 1.0), (11, 1.2), (16, 1.0), (16, 1.2)):
            for width in (1600, 420):
                scale = 2.0
                native_scale = scale * max(1.0, points / 11.0)
                region = SimpleNamespace(width=round(width * scale), view2d=SimpleNamespace(
                    region_to_view=lambda x, y, z=zoom: (100 + x / z, y / z)))
                context = SimpleNamespace(region=region, preferences=SimpleNamespace(
                    system=SimpleNamespace(ui_scale=scale),
                    ui_styles=[SimpleNamespace(widget=SimpleNamespace(points=points))]))
                for state in ({'state': 'idle'}, {'state': 'checking'}):
                    layout = Layout()
                    with patch.object(nc, 'UPDATE_STATUS', state), \
                            patch.object(nc, '_preferences', return_value=prefs):
                        nc._draw_update_header(layout, context)
                    assert len(layout.children) == (1 if width == 1600 else 2)
                    props = [item for item in layout.walk() if item.kind == 'prop']
                    beta = next(item for item in props if item.props['name'] == 'accept_beta_updates')
                    selector = next(item for item in props if item.props['name'] == 'update_release')
                    available = region.width / zoom - 48 * native_scale
                    controls_width = available / 2 if width == 1600 else available
                    beta_factor = beta.parent.parent.props['factor']
                    beta_width = ((1 - beta_factor) if width == 1600 else beta_factor) * controls_width
                    assert abs(beta_width - 50 * native_scale) < 0.001
                    selector_space = controls_width if width == 1600 else controls_width - beta_width
                    buttons_width = (1 - selector.parent.parent.props['factor']) * selector_space
                    text_width = nc._text_width(nc._ui_text('Update'), round(13 * native_scale))
                    assert abs(buttons_width - max(70 * native_scale, text_width + 44 * native_scale)) < 0.001
                    assert beta.props['text'] == 'Beta'
                    labels = [item for item in layout.walk() if item.kind == 'label']
                    assert labels[0].props['text'] == f'Node Console v{nc.ADDON_VERSION}'
                    assert not hasattr(labels[0].parent, 'ui_units_x')
                    assert labels[0].parent.parent is labels[1].parent.parent
                    cases += 1
    sample = {'id': 'test-snippet', 'name': 'Example', 'tree_type': 'GeometryNodeTree',
              'category': 'NONE', 'node_count': 3, 'link_count': 2}
    assert 'feedback_text' not in nc.ENS_AddonPreferences.__annotations__
    assert not any(cls.bl_idname == 'node_console.report_bug' for cls in nc.classes)
    social_titles = {'en_US': 'Technical Dictionary', 'zh_HANS': '飞书技术字典',
                     'ja_JP': '技術リファレンス', 'ko_KR': '기술 자료실',
                     'ru_RU': 'Технический справочник', 'es': 'Diccionario técnico'}
    social_urls = [
        'https://space.bilibili.com/25142156?spm_id_from=333.1007.0.0',
        'https://xhslink.com/m/6zzQ97wiPAI',
        'https://dcnztj4835bh.feishu.cn/wiki/ClI2wK0nyi2DvckJA5wcbmf7nBe?from=from_copylink',
        'https://github.com/AnthemZhou']
    with patch.object(nc, '_load_asset_index', return_value=[]), \
            patch.object(nc, '_load_favorite_meta', return_value={}), \
            patch.object(nc, '_load_identifier_tree_meta', return_value={}), \
            patch.object(nc, '_load_favorites', return_value=set()), \
            patch.object(nc, '_load_shortcuts', return_value=[]), \
            patch.object(nc, '_shortcut_conflict_labels', return_value=[]), \
            patch.object(nc, '_snippet_search_snapshot') as snippets:
        for language in social_titles:
            bpy.context.preferences.view.language = language
            for width in (1200, 420):
                context = SimpleNamespace(region=SimpleNamespace(width=width),
                    preferences=SimpleNamespace(system=SimpleNamespace(ui_scale=1.0)))
                for expanded, saved in ((False, [sample]), (True, []), (True, [sample])):
                    prefs = SimpleNamespace(layout=Layout(), snippet_nodes_expanded=expanded)
                    snippets.reset_mock()
                    snippets.return_value = {'snippets': saved}
                    nc.ENS_AddonPreferences.draw(prefs, context)
                    if expanded:
                        snippets.assert_called_once_with()
                    else:
                        snippets.assert_not_called()
                    snippet_box, library_box = prefs.layout.children[-2:]
                    labels = lambda box: [x.props['text'] for x in box.walk() if x.kind == 'label']
                    assert snippet_box.kind == library_box.kind == 'box'
                    assert labels(snippet_box)[0] == nc._ui_text('Snippet Nodes')
                    assert labels(library_box)[0] == nc._ui_text('Snippet Libraries')
                    assert nc._ui_text('Default Library') in labels(library_box)
                    assert any(x.kind == 'prop' and x.props['name'] == 'snippet_library_path'
                               for x in library_box.walk())
                    assert not any(x.kind == 'operator' for x in library_box.walk())
                    toggle = next(x for x in snippet_box.walk() if x.kind == 'prop')
                    assert toggle.props['icon'] == ('TRIA_DOWN' if expanded else 'TRIA_RIGHT')
                    remove = [x for x in snippet_box.walk() if x.kind == 'operator']
                    if expanded and saved:
                        assert len(remove) == 1 and remove[0].snippet_id == sample['id']
                        assert remove[0].props['name'] == nc.NODECONSOLE_OT_RemoveSnippet.bl_idname
                        assert any(f"3 {nc._ui_text('nodes')} / 2 {nc._ui_text('links')}" in text
                                   for text in labels(snippet_box))
                    else:
                        assert not remove
                        assert labels(snippet_box)[1:] == ([nc._ui_text('No snippet nodes')] if expanded else [])
                    assert not any(x.kind == 'prop' and x.props['name'] == 'feedback_text'
                                   or x.kind == 'operator' and x.props['name'] == 'node_console.report_bug'
                                   for x in prefs.layout.walk())
                    settings_box = prefs.layout.children[0]
                    assert settings_box.kind == 'box'
                    asset_toggle = next(x for x in settings_box.walk()
                                        if x.kind == 'prop' and x.props['name'] == 'scan_asset_libraries')
                    assert asset_toggle.props['text'] == (
                        '显示用户自定义的缓存资产节点' if language == 'zh_HANS' else 'Show Cached Asset Nodes')
                    social_index = 1 if width == 1200 else 2
                    social = settings_box.children[social_index]
                    assert social.kind == 'split' and social.props['factor'] == 0.5
                    buttons = [x for x in social.walk() if x.kind == 'operator']
                    assert [button.url for button in buttons] == social_urls
                    prefixes = ('B站:', '小红书:', '飞书:') if language == 'zh_HANS' else (
                        'Bilibili:', 'Xiaohongshu:', 'Feishu:')
                    expected = [f'{prefixes[0]} 周圣宇_Anthem', f'{prefixes[1]} 一周不剩',
                                f'{prefixes[2]} {social_titles[language]}', f'GitHub: Node Console v{nc.ADDON_VERSION}']
                    assert [' '.join(button.props['text'].split()) for button in buttons] == expected
                    assert all(button.props['translate'] is False for button in buttons)
                    account_indices = [buttons[0].props['text'].index('周圣宇_Anthem'),
                                       buttons[1].props['text'].index('一周不剩')]
                    assert account_indices[0] == account_indices[1]
                    assert all(button.props['text'][index - 1] == ' '
                               for button, index in zip(buttons, account_indices))
                    assert all(x.kind in {'row', 'split'} for x in settings_box.children[:social_index])
                    assert settings_box.children[social_index + 1].kind == 'separator'
                    assert settings_box.children[social_index + 1].props['type'] == 'LINE'
                    cases += 1
    for language, locale, translate, expected_language in (
            ('DEFAULT', 'ja_JP', True, 'ja'), ('DEFAULT', 'zh_HANS', True, 'zh'),
            ('es_ES', 'en_US', True, 'es'), ('ko-KR', 'en_US', True, 'ko'),
            ('fr_FR', 'en_US', True, 'en'), ('zh_HANS', 'zh_HANS', False, 'en')):
        view = SimpleNamespace(language=language, use_translate_interface=translate)
        wrapper = SimpleNamespace(context=SimpleNamespace(preferences=SimpleNamespace(view=view)),
                                  app=SimpleNamespace(translations=SimpleNamespace(locale=locale)))
        with patch.object(nc, 'bpy', wrapper), patch.object(nc, '_search_language', return_value='ru_RU') as search_language:
            assert nc._social_link_labels() == nc.SOCIAL_LINK_LABELS[expected_language]
            search_language.assert_not_called()
        cases += 1
    print('PREFERENCES_UI_REGRESSION', bpy.app.version_string, cases, 'passed', flush=True)


if __name__ == '__main__':
    main()
