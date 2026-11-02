"""Native UI golden rows, language independence, identity and ranking regressions."""
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
spec = importlib.util.spec_from_file_location('NCNativeTest',ROOT/'__init__.py',submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._settings_path = lambda: Path(os.environ['BLENDER_USER_CONFIG'])/'test-settings.json'
nc._preferences = lambda: None
sentinel = {'favorites':['keep-me'], 'shortcuts':['keep-shortcut'], 'usage':{'keep-me':42}}
nc._write_settings(sentinel)
nc._refresh_asset_index()
fixture = json.loads((ROOT/'tools/fixtures/native_search_5_2_2.json').read_text())
report = {'version':bpy.app.version_string, 'golden_queries':0, 'golden_rows':0,
          'queries':0, 'failures':[], 'trees':{}, 'equal_score_differences':[]}
for tree_id in ('GeometryNodeTree','ShaderNodeTree','CompositorNodeTree'):
    tree = bpy.data.node_groups.new('Native search test',tree_id)
    context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id,
        shader_type='OBJECT', node_tree_sub_type='SCENE' if tree_id=='CompositorNodeTree' else 'MODIFIER',
        id_from=bpy.context.object), engine='BLENDER_EEVEE')
    nc._clear_search_caches()
    nc._rebuild_search_entries(context)
    snapshot = [(entry.identifier,entry.menu_paths) for entry in nc.NODE_SEARCH_ENTRIES]
    for entry in nc.NODE_SEARCH_ENTRIES:
        for text in (entry.english, entry.chinese, entry.leaf_pinyin_compact,
                     entry.leaf_pinyin_initials, *entry.aliases, 'she zhi', '\u8bbe\u7f6e'):
            query = nc._normalize(text)
            if query:
                assert nc._extension_match(entry, query) == nc._extension_match(
                    entry, query, nc._query_match_parts(entry, query)), (entry.identifier, query)
    original_language = bpy.context.preferences.view.language
    original_iface = bpy.app.translations.pgettext_iface
    for language in ('en_US','zh_HANS'):
        bpy.context.preferences.view.language = language
        captured, errors = nc.node_menu_search.collect(context,nc.node_registry.official_chinese_label)
        assert not errors, errors
        assert bpy.context.preferences.view.language == language
        assert bpy.app.translations.pgettext_iface is original_iface
        # Execute original functions with actual Blender translations as an independent
        # check of our private bilingual namespaces (same traversal, different labels).
        class DirectCollector(nc.node_menu_search.Collector):
            def function(self, function):
                return function
        bpy.context.preferences.view.use_translate_interface = True
        actual = DirectCollector(context,bpy.app.translations.pgettext_iface)
        actual.draw('NODE_MT_add',[])
        actual_paths = {separator.join(parts) for operator,separator,parts,weight,props in actual.rows
                        if operator in {'node.add_node','node.add_zone'}}
        language_index = 0 if language=='en_US' else 1
        assert {row[language_index] for rows in captured.values() for row in rows} == actual_paths
        nc._rebuild_search_entries(context)
        assert snapshot == [(entry.identifier,entry.menu_paths) for entry in nc.NODE_SEARCH_ENTRIES]
        if bpy.app.version[:3] == (5,2,2):
            for editor,query,expected in fixture['samples']:
                if editor != tree_id:
                    continue
                result = nc._search_entries(query,set())
                names = [entry.english for entry in result[:len(expected)]]
                report['golden_queries'] += 1
                report['golden_rows'] += len(expected)
                if names != expected or (not expected and result):
                    report['failures'].append([tree_id,language,query,expected,names])
            for editor,query,expected in fixture.get('tie_samples', []):
                if editor != tree_id:
                    continue
                result = nc._search_entries(query,set())
                by_name = {entry.english: entry for entry in result}
                def tie_key(entry):
                    item = entry._native_items[1][0]
                    return (nc.native_search.score(nc.native_search.words(query)[0], item),
                            item.weight, item.main_length, item.total_length)
                assert [entry.english for entry in result[:5]] == expected[:5]
                for position, name in enumerate(expected):
                    assert tie_key(result[position]) == tie_key(by_name[name])
                    if result[position].english != name:
                        report['equal_score_differences'].append(
                            [tree_id,language,query,position+1,name,result[position].english])
        for query,label in [('noise','Noise Texture'),('NOISE','Noise Texture'),
                            ('niose','Noise Texture'),('nt','Noise Texture'),
                            ('zaobo','Noise Texture'),('zbwl','Noise Texture')]:
            result = nc._search_entries(query,set())
            report['queries'] += 1
            assert any(entry.english == label for entry in result), (tree_id,language,query)
            if tree_id != 'CompositorNodeTree':
                assert result[0].english == label, (tree_id,language,query,[e.english for e in result[:4]])
        result = nc._search_entries('noise',set())
        favorite = next(entry for entry in result if entry.english=='White Noise Texture')
        assert nc._search_entries('noise',{favorite.identifier})[0].identifier == favorite.identifier
        assert nc._search_entries('noise',set()) == result
        assert nc._search_entries('   ',set()) == []
    bpy.context.preferences.view.language = original_language
    timings = []
    for _ in range(3):
        for query in ('mesh','add','line','instance','nt','niose','噪波','模糊','shili','zbwl'):
            start = time.perf_counter()
            nc._search_entries(query,set())
            timings.append((time.perf_counter()-start)*1000)
    key = nc._search_index_cache_key(context)
    def paths_for_context():
        paths, errors = nc.node_menu_search.collect(context,nc.node_registry.official_chinese_label)
        assert not errors, errors
        return {identity[0] for identity in paths}
    original_types = paths_for_context()
    context.engine = 'CYCLES'
    assert nc._search_index_cache_key(context) != key
    if tree_id == 'ShaderNodeTree':
        assert 'ShaderNodeShaderToRGB' in original_types
        assert 'ShaderNodeShaderToRGB' not in paths_for_context()
    context.engine = 'BLENDER_EEVEE'
    context.space_data.shader_type = 'WORLD'
    assert nc._search_index_cache_key(context) != key
    if tree_id == 'ShaderNodeTree':
        assert 'ShaderNodeBackground' not in original_types
        assert 'ShaderNodeBackground' in paths_for_context()
    if tree_id == 'GeometryNodeTree' and bpy.app.version[:2] >= (5,2):
        context.space_data.node_tree_sub_type = 'TOOL'
        assert 'GeometryNodeToolMousePosition' not in original_types
        assert 'GeometryNodeToolMousePosition' in paths_for_context()
    report['trees'][tree_id] = {'entries':len(snapshot),'median_ms':statistics.median(timings),'max_ms':max(timings)}
    bpy.data.node_groups.remove(tree)
assert all(nc._load_settings()[key] == value for key,value in sentinel.items())
output = Path(sys.argv[sys.argv.index('--')+1])
output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('NATIVE_SEARCH_REGRESSION',report,flush=True)
assert not report['failures'], 'Native UI golden order mismatches; see report'
