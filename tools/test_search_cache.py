"""Cache lifecycle regressions in an isolated factory-startup Blender process."""
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location(
        'NCCacheTest', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    passed = []

    first = nc.NodeSearchEntry('first', 'Group', 'Cache Sample', 'Cache Sample',
                               'Cache Sample', '', 'ASSET', search_text='cache sample')
    second = replace(first, identifier='second')
    nc.NODE_SEARCH_ENTRIES[:] = [first, second]
    serialized = asdict(first)
    with patch.object(nc, '_prepare_match_data', wraps=nc._prepare_match_data) as prepare:
        assert nc._search_entries('cache', set()) == [first, second]
        assert nc._search_entries('cache', {'second'}) == [second, first]
        assert nc._search_entries('cache', set()) == [first, second]
        assert prepare.call_count == 2
    assert asdict(first) == serialized
    assert '_match_data' not in serialized
    passed.extend(('entry preprocessing reused', 'favorites updated immediately',
                   'cache excluded from persistence'))

    changed = replace(first, english='Renamed Sample', chinese='Renamed Sample',
                      label='Renamed Sample', search_text='renamed sample',
                      aliases=('cachealias',), leaf_pinyin_compact='', root_pinyin_compact='')
    assert '_match_data' not in changed.__dict__
    assert nc._query_match_parts(changed, 'renamed')['leaf_prefix']
    assert nc._query_match_parts(changed, 'cachealias')['leaf_exact']
    assert changed._match_data is not first._match_data
    passed.append('replacement entry has fresh names and aliases')

    with patch.object(nc, '_query_match_parts', wraps=nc._query_match_parts) as match:
        assert nc._search_entries('zzzznomatch', set()) == []
        assert match.call_count == len(nc.NODE_SEARCH_ENTRIES)
        match.reset_mock()
        assert nc._search_entries('  ', set()) == []
        assert match.call_count == 0
    passed.extend(('weak-pinyin retry reuses matches', 'blank query skips matching'))

    for index in range(8500):
        nc._normalize(f'Cache Probe {index}')
        nc._search_words(f'Cache Probe {index}')
        nc._officialish_query_key(f'Cache Probe {index}')
    assert nc._normalize.cache_info().currsize <= 8192
    assert nc._search_words.cache_info().currsize <= 8192
    assert nc._officialish_query_key.cache_info().currsize <= 256
    nc._clear_search_caches()
    for function in (nc._normalize, nc._search_words, nc._officialish_query_key):
        assert function.cache_info().currsize == 0
    assert nc.NODE_SEARCH_ENTRIES == [first, second]
    passed.extend(('bounded string caches', 'text cache reset preserves active entries'))

    with tempfile.TemporaryDirectory(prefix='nc-cache-test-') as directory:
        nc._settings_path = lambda: Path(directory) / 'settings.json'
        nc._preferences = lambda: None
        tree = bpy.data.node_groups.new('Cache Test Editor', 'GeometryNodeTree')
        group = bpy.data.node_groups.new('Cache Before Rename', 'GeometryNodeTree')
        context = SimpleNamespace(space_data=SimpleNamespace(
            edit_tree=tree, tree_type=tree.bl_idname, cursor_location=(0, 0)))
        try:
            nc._rebuild_search_entries(context)
            assert any(e.english == group.name for e in nc._search_entries('cache before', set()))
            group.name = 'Cache After Rename'
            nc._rebuild_search_entries(context)
            assert not any(e.english == 'Cache Before Rename' for e in nc.NODE_SEARCH_ENTRIES)
            assert any(e.english == group.name for e in nc._search_entries('cache after', set()))
            bpy.data.node_groups.remove(group)
            group = None
            nc._rebuild_search_entries(context)
            assert not any(e.english == 'Cache After Rename' for e in nc.NODE_SEARCH_ENTRIES)
            passed.append('live group rename and removal survive warm rebuild')
        finally:
            if group is not None:
                bpy.data.node_groups.remove(group)
            bpy.data.node_groups.remove(tree)

    # Cached snippet entries still observe favorites, edits and external deletion.
    snippets = [dict(id='one', name='Sample One', category='NONE', tree_type='GeometryNodeTree'),
                dict(id='two', name='Sample Two', category='NONE', tree_type='GeometryNodeTree')]
    with tempfile.TemporaryDirectory(prefix='nc-snippet-cache-') as directory:
        nc._snippets_path = lambda: Path(directory) / 'snippets.json'
        nc._save_snippets(snippets)
        assert nc._search_snippets('', 'GeometryNodeTree', set())[0].identifier == 'snippet:one'
        with patch.object(nc, '_snippet_to_entry', wraps=nc._snippet_to_entry) as prepare:
            assert nc._search_snippets('', 'GeometryNodeTree', {'snippet:two'})[0].identifier == 'snippet:two'
            assert nc._search_snippets('sample', 'GeometryNodeTree', set())
            assert prepare.call_count == 0
        passed.append('snippet entries reused across keystrokes and favorites')
        snippets[1]['name'] = 'Renamed Snippet'
        nc._save_snippets(snippets)
        assert nc._search_snippets('renamed', 'GeometryNodeTree', set())[0].identifier == 'snippet:two'
        snippets.pop()
        nc._snippets_path().write_text(json.dumps({'snippets': snippets}), encoding='utf-8')
        assert not nc._search_snippets('renamed', 'GeometryNodeTree', set())
        with patch.object(nc, '_display_mode', return_value='CHINESE'):
            with patch.object(nc, '_snippet_to_entry', wraps=nc._snippet_to_entry) as prepare:
                nc._search_snippets('sample', 'GeometryNodeTree', set())
                assert prepare.call_count == 1
        passed.append('snippet display changes invalidate cached entries')
        nc._snippets_path().write_text('{"version": "invalid", "snippets": []}', encoding='utf-8')
        assert nc._load_snippet_store() == {'version': nc.SNIPPET_SCHEMA_VERSION, 'snippets': []}
        assert not nc._search_snippets('', 'GeometryNodeTree', set())
        passed.append('invalid snippet schema value does not crash search')
    passed.append('snippet favorites, rename and deletion remain live')

    with tempfile.TemporaryDirectory(prefix='nc-prepared-index-') as directory:
        nc._settings_path = lambda: Path(directory) / 'settings.json'
        nc._preferences = lambda: None
        nc._clear_search_caches()
        sentinel = {'favorites': ['keep'], 'shortcuts': ['keep'], 'usage': {'keep': 42}}
        nc._write_settings(sentinel)
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Prepared index test', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id))
            try:
                nc._rebuild_search_entries(context)
                expected = [asdict(entry) for entry in nc.NODE_SEARCH_ENTRIES]
                assert len({entry['identifier'] for entry in expected}) == len(expected)
                queries = {'join', 'math', 'line', 'add', 'noise', 'shili', '\u5b9e\u4f8b'}
                for entry in nc.NODE_SEARCH_ENTRIES:
                    queries.update((entry.english, entry.chinese, entry.leaf_pinyin_initials))
                ranking = {q: [e.identifier for e in nc._search_entries(q, set())] for q in queries}
                nc._clear_search_caches()
                with patch.object(nc, '_iter_menu_entries', side_effect=AssertionError('menu reparsed')),\
                        patch.object(nc.node_registry, 'catalog', side_effect=AssertionError('catalog reloaded')):
                    nc._rebuild_search_entries(context)
                    assert [asdict(entry) for entry in nc.NODE_SEARCH_ENTRIES] == expected
                    for query in queries:
                        assert [e.identifier for e in nc._search_entries(query, set())] == ranking[query]
                    with patch.object(nc, '_entry_from_cache', side_effect=AssertionError('entries reconstructed')):
                        nc._rebuild_search_entries(context)
                with patch.object(nc, '_display_mode', return_value='CHINESE'):
                    nc._rebuild_search_entries(context)
                    assert all(e.label == nc._entry_label(e.english, e.chinese) for e in nc.NODE_SEARCH_ENTRIES)
                passed.append(tree_id + ': cold/disk/memory names, colors, pinyin and ranking match')
            finally:
                bpy.data.node_groups.remove(tree)
        assert all(nc._load_settings()[key] == value for key, value in sentinel.items())
        passed.append('index rebuild preserves favorites, shortcuts and usage')

        tree = bpy.data.node_groups.new('Cache invalidation', 'GeometryNodeTree')
        context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree.bl_idname))
        class NCCacheRegisteredNode(bpy.types.Node):
            bl_idname = 'NCCacheRegisteredNode'
            bl_label = 'Cache Registration Probe'

            @classmethod
            def poll(cls, node_tree):
                return node_tree.bl_idname == 'GeometryNodeTree'

        try:
            nc._rebuild_search_entries(context)
            before = nc._search_index_cache_key(context)
            bpy.utils.register_class(NCCacheRegisteredNode)
            try:
                assert nc._search_index_cache_key(context) != before
                with patch.object(nc, '_iter_menu_entries', wraps=nc._iter_menu_entries) as menus:
                    nc._rebuild_search_entries(context)
                    assert menus.called
            finally:
                bpy.utils.unregister_class(NCCacheRegisteredNode)
            nc._rebuild_search_entries(context)
            assert nc._search_index_cache_key(context) == before
            assert not any(e.node_type == 'NCCacheRegisteredNode' for e in nc.NODE_SEARCH_ENTRIES)
            passed.append('registering and disabling another node add-on invalidates the index')

            asset = Path(directory) / 'available.blend'
            asset.touch()
            nc._save_asset_index([dict(path=str(asset), name='Cache Asset', tree_type=tree.bl_idname)])
            nc._rebuild_search_entries(context)
            assert any(e.asset_name == 'Cache Asset' for e in nc.NODE_SEARCH_ENTRIES)
            asset.unlink()
            nc._rebuild_search_entries(context)
            assert not any(e.asset_name == 'Cache Asset' for e in nc.NODE_SEARCH_ENTRIES)
            passed.append('missing external asset files are filtered even with a prepared index')
            nc._write_settings(sentinel)
            nc._rebuild_search_entries(context)
            assert nc._load_search_index_cache(context)
            passed.append('externally removed index is rebuilt and persisted again')
            data = nc._load_settings()
            key = nc._search_index_cache_key(context)
            data['search_index_cache'][key] = [entry for entry in data['search_index_cache'][key]
                                               if entry['node_type'] != 'ShaderNodeMath']
            nc._write_settings(data)
            nc._rebuild_search_entries(context)
            assert any(e.node_type == 'ShaderNodeMath' for e in nc.NODE_SEARCH_ENTRIES)
            passed.append('incomplete persisted index cannot hide available node types')
        finally:
            bpy.data.node_groups.remove(tree)

    report = {'version': bpy.app.version_string, 'passed': passed}
    if '--' in sys.argv:
        Path(sys.argv[sys.argv.index('--') + 1]).write_text(
            json.dumps(report, indent=2), encoding='utf-8')
    print('CACHE_REGRESSION', bpy.app.version_string, len(passed), 'passed', flush=True)


if __name__ == '__main__':
    main()
