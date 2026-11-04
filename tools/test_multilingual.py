"""Official selected-language indexes; run only through run_isolated_blender.py."""
import gettext
import importlib.util
import json
import os
import re
from pathlib import Path
import statistics
import sys
import time
import unicodedata
from types import SimpleNamespace
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]


def main():
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
    bpy.context.preferences.use_preferences_save = False
    spec = importlib.util.spec_from_file_location('NCMultilingual', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    nc.register()
    addon = bpy.context.preferences.addons.new()
    addon.module = nc.ADDON_ID
    prefs = addon.preferences
    nc._load_preferences_from_settings()
    assert prefs.search_language == nc._default_search_language()
    assert prefs.display_mode == ('ENGLISH' if prefs.search_language == 'en_US' else 'ENGLISH_CHINESE')
    prefs.scan_asset_libraries = False
    nc._write_settings({'favorites': ['saved-id'], 'usage': {'saved-id': 42},
                        'shortcuts': ['saved-id'], 'unknown_setting': [1, 2]})
    baseline_settings = nc._load_settings()
    baseline_ui = (bpy.context.preferences.view.language, bpy.context.preferences.view.use_translate_interface)
    report = {'version': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode(),
              'locales': {}, 'search_checks': 0, 'creation_checks': 0,
              'typing_variants': 0, 'favorite_checks': 0, 'snippet_checks': 0}
    identities = {}
    for code, name, locales in nc.node_registry.LANGUAGES:
        prefs.search_language = code
        prefs.display_mode = 'ENGLISH' if code == 'en_US' else 'ENGLISH_CHINESE'
        assert not nc.SEARCH_QUERY_CACHE
        # Read the installed MO separately as the oracle (not the add-on helper).
        oracle = gettext.NullTranslations()
        for locale in locales:
            path = Path(bpy.utils.resource_path('LOCAL')) / 'datafiles/locale' / locale / 'LC_MESSAGES/blender.mo'
            if path.is_file():
                with path.open('rb') as source:
                    oracle = gettext.GNUTranslations(source)
                break
        if locales:
            assert isinstance(oracle, gettext.GNUTranslations), (code, 'official catalog not found')
        info = report['locales'][code] = {'name': name, 'trees': {}}
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Multilingual test', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id, cursor_location=(0, 0)), engine='BLENDER_EEVEE')
            started = time.perf_counter()
            nc._rebuild_search_entries(context)
            elapsed = (time.perf_counter() - started) * 1000
            entries = list(nc.NODE_SEARCH_ENTRIES)
            entry_ids = [(e.identifier, e.node_type, e.settings) for e in entries]
            if tree_id in identities:
                assert identities[tree_id] == entry_ids, (code, tree_id, 'identities changed')
            else:
                identities[tree_id] = entry_ids
            assert all(e.language == code for e in entries)
            if code != 'zh_HANS':
                assert all(not e.leaf_pinyin_compact and not e.root_pinyin_compact for e in entries)
                assert all(alias.isascii() for e in entries for alias in e.aliases if e.kind == 'NODE')
            translated = 0
            samples, latency = [], []
            for entry in entries:
                if entry.kind != 'NODE':
                    continue
                node = nc._add_builtin_node(context, entry)
                assert node.bl_idname == entry.node_type
                tree.nodes.remove(node)
                report['creation_checks'] += 1
                if not entry.settings and entry.english == bpy.types.Node.bl_rna_get_subclass(entry.node_type).name:
                    rna = bpy.types.Node.bl_rna_get_subclass(entry.node_type)
                    expected = oracle.pgettext(rna.translation_context, entry.english)
                    if expected == entry.english:
                        expected = oracle.gettext(entry.english)
                    if code != 'zh_HANS':
                        assert entry.chinese == expected, (code, entry.english, entry.chinese, expected)
                    translated += entry.chinese != entry.english
                    if entry.chinese != entry.english and len(samples) < 8:
                        samples.append([entry.english, entry.chinese])
                if entry.native_hidden:
                    continue
                # All names, English and selected language, including operation variants.
                for query in (entry.english.split(' > ')[-1], entry.chinese.split(' > ')[-1]):
                    started = time.perf_counter()
                    results = nc._search_entries(query, set())
                    latency.append((time.perf_counter() - started) * 1000)
                    assert entry.identifier in {e.identifier for e in results}, (code, tree_id, entry.english, query)
                    report['search_checks'] += 1
                # Case, whitespace, NFC/NFD, and full-width queries preserve ranking.
                if code != 'zh_HANS' and entry.chinese != entry.english:
                    query = entry.chinese.split(' > ')[-1]
                    expected = [e.identifier for e in nc._search_entries(query, set())]
                    for variant in (query.upper(), unicodedata.normalize('NFD', query), '  ' + query.replace(' ', '  ') + '  '):
                        actual = [e.identifier for e in nc._search_entries(variant, set())]
                        assert actual == expected, (code, query, variant)
                        report['search_checks'] += 1
                    variants = {nc.node_registry.search_key(query, code)}
                    if code == 'ko_KR':
                        variants.add(query.replace(' ', ''))
                        for word in re.findall(r'[가-힣]{2,}', query):
                            variants.add(nc.search_language.initials(word))
                            variants.add(word[0] + nc.search_language.initials(word[1]))
                    for variant in variants:
                        found = nc._search_entries(variant, set())
                        assert entry.identifier in {e.identifier for e in found}, (code, tree_id, query, variant)
                        report['typing_variants'] += 1
            if code != 'zh_HANS':
                assert nc._search_entries('ＮＯＩＳＥ', set()) == nc._search_entries('noise', set())
            if locales:
                assert translated >= 70, (code, tree_id, 'unexpectedly low translation coverage', translated)
            target = next(e for e in entries if e.english == ('Blur' if tree_id == 'CompositorNodeTree' else 'Noise Texture'))
            baseline = nc._search_entries(target.chinese, set())
            assert nc._search_entries(target.chinese, {target.identifier})[0] == target
            assert nc._search_entries(target.chinese, set()) == baseline
            report['favorite_checks'] += 2
            snapshot = [(e.identifier, e.chinese, e.language) for e in entries]
            nc._clear_search_caches()
            nc._rebuild_search_entries(context)
            assert snapshot == [(e.identifier, e.chinese, e.language) for e in nc.NODE_SEARCH_ENTRIES]
            # A cache hit need not load any translation catalog.
            assert nc.node_registry._catalog is None
            info['trees'][tree_id] = dict(entries=len(entries), translated_base_nodes=translated,
                build_ms=round(elapsed, 2), median_search_ms=round(statistics.median(latency), 3), samples=samples)
            bpy.data.node_groups.remove(tree)
        names = {'zh_HANS': ('随机选择', 'suijixuanze'), 'ja_JP': ('ノイズ設定', 'のいず'),
                 'ko_KR': ('노이즈 설정', 'ㄴㅇㅈ'), 'ru_RU': ('Объём', 'объем'),
                 'es': ('Posición', 'posicion'), 'en_US': ('Random Selection', 'random selection')}
        title, query = names[code]
        snippets = [nc._snippet_to_entry(dict(id=str(i), name=title + str(i), category='NONE')) for i in range(2)]
        for text in (query, unicodedata.normalize('NFD', title), title):
            found = nc._search_entries_from_list(snippets, text)
            assert len(found) == 2, (code, title, text)
            assert nc._search_entries_from_list(snippets, text, {snippets[-1].identifier})[0] == snippets[-1]
            assert nc._search_entries_from_list(snippets, text) == found
            assert snippets[0].label == title + '0'
            report['snippet_checks'] += 4
        for mode, _label, _description, _value in nc._display_mode_items(prefs, None):
            prefs.display_mode = mode
            assert prefs.display_mode == mode
        assert nc._display_mode_items(prefs, None)[0 if code == 'en_US' else 1][1] == name
        assert (bpy.context.preferences.view.language, bpy.context.preferences.view.use_translate_interface) == baseline_ui
        assert all(nc._load_settings()[k] == v for k, v in baseline_settings.items())
        print('MULTILINGUAL_LOCALE_OK', code, flush=True)

    # Missing catalogs/names are English, not fabricated translations.
    for code, _name, _locales in nc.node_registry.LANGUAGES:
        assert 'PCA' in nc.node_registry.search_aliases('Principal Components', code)
        assert 'Input Object' in nc.node_registry.search_aliases('Object', code)
    nc.node_registry.clear()
    with patch.object(nc.node_registry.Path, 'is_file', return_value=False):
        assert nc.node_registry.official_label('Noise Texture', language='ja_JP') == 'Noise Texture'
    assert nc.node_registry.official_label('Untranslated Test Node', language='es') == 'Untranslated Test Node'
    prefs.search_language = 'ja_JP'
    prefs.display_mode = 'CHINESE_ENGLISH'
    prefs.shortcut_key = 'F'
    nc._save_preference_settings()
    with patch.object(nc, '_save_preference_settings'):
        prefs.search_language = 'es'
        prefs.display_mode = 'ENGLISH'
    nc._load_preferences_from_settings()
    assert (prefs.search_language, prefs.display_mode, prefs.shortcut_key) == ('ja_JP', 'CHINESE_ENGLISH', 'F')
    nc.unregister()
    bpy.context.preferences.addons.remove(addon)
    output = Path(sys.argv[sys.argv.index('--') + 1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('MULTILINGUAL_OK', report['search_checks'], report['creation_checks'], flush=True)


if __name__ == '__main__':
    main()
