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

    # Snippet content is not cached: favorites and edits remain live too.
    snippets = [dict(id='one', name='Sample One', category='NONE', tree_type='GeometryNodeTree'),
                dict(id='two', name='Sample Two', category='NONE', tree_type='GeometryNodeTree')]
    with patch.object(nc, '_load_snippets', return_value=snippets):
        assert nc._search_snippets('', 'GeometryNodeTree', set())[0].identifier == 'snippet:one'
        assert nc._search_snippets('', 'GeometryNodeTree', {'snippet:two'})[0].identifier == 'snippet:two'
        snippets[1]['name'] = 'Renamed Snippet'
        assert nc._search_snippets('renamed', 'GeometryNodeTree', set())[0].identifier == 'snippet:two'
        snippets.pop()
        assert not nc._search_snippets('renamed', 'GeometryNodeTree', set())
    passed.append('snippet favorites, rename and deletion remain live')

    report = {'version': bpy.app.version_string, 'passed': passed}
    if '--' in sys.argv:
        Path(sys.argv[sys.argv.index('--') + 1]).write_text(
            json.dumps(report, indent=2), encoding='utf-8')
    print('CACHE_REGRESSION', bpy.app.version_string, len(passed), 'passed', flush=True)


if __name__ == '__main__':
    main()
