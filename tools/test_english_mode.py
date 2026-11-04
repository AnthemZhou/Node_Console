"""English-only defaults and migration; run in an isolated Blender process."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]
config = Path(os.environ['BLENDER_USER_CONFIG']).resolve()
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == config
bpy.context.preferences.use_preferences_save = False
view = bpy.context.preferences.view
view.language = 'en_US'
view.use_translate_interface = True
spec = importlib.util.spec_from_file_location('NCEnglishMode', ROOT / '__init__.py',
                                             submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._settings_path = lambda: config / 'english-settings.json'
nc.register()
addon = bpy.context.preferences.addons.new()
addon.module = nc.ADDON_ID
prefs = addon.preferences
sentinel = {'favorites': ['saved-id'], 'shortcuts': ['saved-id'],
            'usage': {'saved-id': 42}, 'unknown': {'retain': True}}
cases = []
try:
    def reset(data):
        nc._write_settings(dict(sentinel, **data))
        prefs.property_unset('search_language')
        prefs.property_unset('display_mode')
        nc._load_preferences_from_settings()
        assert all(nc._load_settings()[key] == value for key, value in sentinel.items())

    reset({})
    assert (prefs.search_language, prefs.display_mode) == ('en_US', 'ENGLISH')
    assert len(nc._display_mode_items(prefs, None)) == 1
    assert nc.NODE_LANGUAGE_ITEMS[0][0] == 'en_US'
    assert dict((row[0], row[3]) for row in nc.NODE_LANGUAGE_ITEMS) == {
        'zh_HANS': 0, 'ja_JP': 1, 'ko_KR': 2, 'ru_RU': 3, 'es': 4, 'en_US': 5}
    cases.append('fresh English UI uses English only; existing RNA values preserved')

    for locale, expected in [('zh_HANS', 'zh_HANS'), ('ja_JP', 'ja_JP'),
                             ('ko_KR', 'ko_KR'), ('ru_RU', 'ru_RU'), ('es', 'es')]:
        view.language = locale
        reset({})
        assert prefs.search_language == expected
        assert prefs.display_mode == 'ENGLISH_CHINESE'
    view.use_translate_interface = False
    reset({})
    assert prefs.search_language == 'en_US'
    view.language = 'en_US'
    view.use_translate_interface = True
    cases.append('fresh defaults follow translated UI, including translation-off English')

    for system_locale, expected in [('en_US', 'en_US'), ('zh_HANS', 'zh_HANS'), ('ja', 'ja_JP')]:
        mock_bpy = SimpleNamespace(context=SimpleNamespace(preferences=SimpleNamespace(
            view=SimpleNamespace(language='DEFAULT', use_translate_interface=True))),
            app=SimpleNamespace(translations=SimpleNamespace(locale=system_locale)))
        with patch.object(nc, 'bpy', mock_bpy):
            assert nc._default_search_language() == expected

    for language, mode in [('zh_HANS', 'CHINESE_ENGLISH'), ('ja_JP', 'CHINESE'),
                           ('en_US', 'ENGLISH_CHINESE')]:
        reset({'search_language': language, 'display_mode': mode})
        assert prefs.search_language == language
        assert prefs.display_mode == ('ENGLISH' if language == 'en_US' else mode)
    reset({'display_mode': 'CHINESE_ENGLISH'})
    assert (prefs.search_language, prefs.display_mode) == ('zh_HANS', 'CHINESE_ENGLISH')
    nc._write_settings(sentinel)
    prefs.property_unset('display_mode')
    with patch.object(nc, '_save_preference_settings'):
        prefs.search_language = 'ko_KR'
        prefs.display_mode = 'CHINESE'
    nc._load_preferences_from_settings()
    assert (prefs.search_language, prefs.display_mode) == ('ko_KR', 'CHINESE')
    cases.append('saved JSON, older display-only settings and native preferences survive')

    prefs.search_language = 'en_US'
    assert prefs.display_mode == 'ENGLISH'
    nc._save_preference_settings()
    with patch.object(nc, '_save_preference_settings'):
        prefs.search_language = 'zh_HANS'
        prefs.display_mode = 'CHINESE_ENGLISH'
    nc._load_preferences_from_settings()
    assert (prefs.search_language, prefs.display_mode) == ('en_US', 'ENGLISH')
    assert all(nc._load_settings()[key] == value for key, value in sentinel.items())
    cases.append('English selection normalizes display and survives settings round trip')

    nc._refresh_asset_index()
    trees = {}
    for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
        tree = bpy.data.node_groups.new('English mode test', tree_id)
        group = bpy.data.node_groups.new('My Group / \u4e2d\u6587', tree_id)
        context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id,
            shader_type='OBJECT', id_from=bpy.context.object), engine='BLENDER_EEVEE')
        try:
            # The English-only index must not load translations or prepare pinyin.
            with (patch.object(nc, '_source_pinyin', side_effect=AssertionError('Unexpected pinyin')),
                    patch.object(nc.node_registry.gettext, 'GNUTranslations',
                                 side_effect=AssertionError('Unexpected translation catalog'))):
                nc._clear_search_caches()
                nc._rebuild_search_entries(context)
                entries = list(nc.NODE_SEARCH_ENTRIES)
                assert all(e.language == 'en_US' for e in entries)
                builtins = [e for e in entries if e.kind in {'NODE', 'ZONE', 'ACTION'}]
                assert all(e.english == e.chinese == e.label for e in builtins)
                assert all(not e.leaf_pinyin_compact and not e.root_pinyin_compact for e in entries)
                labels = {e.identifier: e.label for e in entries}
                queries = {'instance', 'noise', 'line', 'join', 'nt', 'niose', 'add', 'blur'}
                queries.update(e.english for e in builtins if not e.native_hidden)
                english_order = {q: [e.identifier for e in nc._search_entries(q, set())] for q in queries}
                assert nc.SEARCH_PINYIN_INDEX is None
                target = next(e for e in entries if e.english == 'My Group / \u4e2d\u6587')
                assert nc._entry_display_label(target.identifier) == target.english
                assert any(e.identifier == target.identifier for e in nc._search_entries('\u4e2d\u6587', set()))
                view.language = 'zh_HANS'
                nc._clear_search_caches()
                nc._rebuild_search_entries(context)
                assert {e.identifier: e.label for e in nc.NODE_SEARCH_ENTRIES} == labels
                for query, expected in english_order.items():
                    assert [e.identifier for e in nc._search_entries(query, set())] == expected
                view.language = 'en_US'
                nc._clear_search_caches()
                nc._rebuild_search_entries(context)
                assert {e.identifier: e.label for e in nc.NODE_SEARCH_ENTRIES} == labels
            prefs.search_language = 'zh_HANS'
            prefs.display_mode = 'CHINESE_ENGLISH'
            nc._rebuild_search_entries(context)
            assert any(e.chinese != e.english for e in nc.NODE_SEARCH_ENTRIES if e.kind == 'NODE')
            assert set(nc.NODE_ENTRY_BY_ID) == set(labels)
            prefs.search_language = 'en_US'
            nc._rebuild_search_entries(context)
            assert {e.identifier: e.label for e in nc.NODE_SEARCH_ENTRIES} == labels
            trees[tree_id] = {'entries': len(entries), 'language_switch_queries': len(queries)}
        finally:
            bpy.data.node_groups.remove(group)
            bpy.data.node_groups.remove(tree)
    cases.append('English names, unchanged IDs, custom names and language-isolated caches')
    nc.NODE_ENTRY_BY_ID.clear()
    assert nc._entry_display_label('N_example', '\u566a\u6ce2 / Noise Texture') == 'Noise Texture'
    assert nc._entry_display_label('G_example', 'My Group / \u4e2d\u6587') == 'My Group / \u4e2d\u6587'
    snippet = nc._snippet_to_entry({'id': 'custom', 'name': 'My Snippet / \u4e2d\u6587', 'category': 'NONE'})
    assert snippet.label == 'My Snippet / \u4e2d\u6587'
    assert nc._search_entries_from_list([snippet], 'my snippet') == [snippet]
    cases.append('saved built-in labels use English; custom and snippet names are not translated')
    print('ENGLISH_MODE_OK', bpy.app.version_string, json.dumps({'cases': cases, 'trees': trees}), flush=True)
finally:
    nc.unregister()
    bpy.context.preferences.addons.remove(addon)
