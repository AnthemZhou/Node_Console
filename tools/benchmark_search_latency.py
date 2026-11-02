"""Compare fresh/repeated keystrokes and complete rankings with a release ZIP."""
import cProfile
import io
import json
import os
from pathlib import Path
import pstats
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace
from zipfile import ZipFile

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_search_upgrade import load, identity

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ('s', 'sh', 'she', 'she ', 'she z', 'she zh', 'she zhi',
           '\u8bbe', '\u8bbe\u7f6e', 'n', 'no', 'noi', 'nois', 'noise',
           'niose', 'random value', 'line', 'add', 'join', 'shili', 'slhyds',
           'set position', 'SET POSITION', 'set  position', 'zzzzmissing')


def timed(call):
    start = time.perf_counter()
    result = call()
    return (time.perf_counter() - start) * 1000, result


def main():
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
    bpy.context.preferences.use_preferences_save = False
    args = sys.argv[sys.argv.index('--') + 1:]
    report = {'version': bpy.app.version_string, 'trees': {}, 'comparisons': 0}
    with tempfile.TemporaryDirectory(prefix='nc-latency-') as directory:
        temp = Path(directory)
        with ZipFile(args[0]) as archive:
            archive.extractall(temp)
        old = load('NCLatencyOld', temp / 'Node_Console', temp / 'settings.json')
        new = load('NCLatencyNew', ROOT, temp / 'settings.json')
        old._refresh_asset_index()
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Latency comparison', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id), engine='BLENDER_EEVEE')
            results = report['trees'][tree_id] = {}
            try:
                for name, nc in (('before', old), ('after', new)):
                    nc._rebuild_search_entries(context)
                    cold, _ = timed(lambda: nc._search_entries('\u8bbe\u7f6e', set()))
                    novel, repeated = [], []
                    for _ in range(5):
                        for query in QUERIES:
                            if hasattr(nc, 'SEARCH_QUERY_CACHE'):
                                nc.SEARCH_QUERY_CACHE.clear()
                            novel.append(timed(lambda: nc._search_entries(query, set()))[0])
                            repeated.append(timed(lambda: nc._search_entries(query, set()))[0])
                    results[name] = dict(cold_input_ms=cold,
                        uncached_query_ms=statistics.median(novel), repeat_query_ms=statistics.median(repeated))
                assert [identity(e) for e in old.NODE_SEARCH_ENTRIES] == [identity(e) for e in new.NODE_SEARCH_ENTRIES]
                queries = set(QUERIES)
                for e in old.NODE_SEARCH_ENTRIES:
                    for text in (e.english, e.chinese, e.leaf_pinyin_compact, e.leaf_pinyin_initials):
                        queries.update((text, text[:3]))
                queries.discard('')
                for query in sorted(queries):
                    expected = old._search_entries(query, set())
                    favorites = {e.identifier for e in expected[::3]}
                    for fav in (set(), favorites):
                        a = [e.identifier for e in old._search_entries(query, fav)]
                        b = [e.identifier for e in new._search_entries(query, fav)]
                        assert a == b, (tree_id, query, a[:10], b[:10])
                        report['comparisons'] += 1
                results['queries'] = len(queries)
                print(tree_id, results, flush=True)
            finally:
                bpy.data.node_groups.remove(tree)

        # Profile the still-expensive fully invalidated path, separately from timings.
        nc = load('NCLatencyCold', ROOT, temp / 'cold.json')
        tree = bpy.data.node_groups.new('Cold profile', 'GeometryNodeTree')
        try:
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree.bl_idname))
            profiler = cProfile.Profile()
            profiler.runcall(nc._rebuild_search_entries, context)
            stream = io.StringIO()
            pstats.Stats(profiler, stream=stream).sort_stats('cumtime').print_stats(30)
            report['cold_profile'] = stream.getvalue()
            print(stream.getvalue(), flush=True)
        finally:
            bpy.data.node_groups.remove(tree)
    Path(args[1]).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('LATENCY_PARITY_OK', report['comparisons'], flush=True)


if __name__ == '__main__':
    main()
