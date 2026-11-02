"""Measure locale keystrokes before/after; ranking is tested separately."""
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace
from zipfile import ZipFile

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_search_upgrade import load
from audit_language_experience import PROBES, ENGLISH

ROOT = Path(__file__).resolve().parents[1]


def main():
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
    bpy.context.preferences.use_preferences_save = False
    args = sys.argv[sys.argv.index('--') + 1:]
    report = {'version': bpy.app.version_string, 'cases': []}
    with tempfile.TemporaryDirectory(prefix='nc-language-latency-') as directory:
        temp = Path(directory)
        with ZipFile(args[0]) as archive:
            archive.extractall(temp)
        old = load('NCLanguageLatencyOld', temp / 'Node_Console', temp / 'old-settings.json')
        new = load('NCLanguageLatencyNew', ROOT, temp / 'new-settings.json')
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Language latency', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id), engine='BLENDER_EEVEE')
            for language, probes in PROBES.items():
                row = dict(tree=tree_id, language=language)
                queries = list(ENGLISH) + [query for query, _ in probes]
                for name, nc in (('before', old), ('after', new)):
                    nc._search_language = lambda: language
                    nc._clear_search_caches()
                    nc._rebuild_search_entries(context)
                    cold_start = time.perf_counter()
                    nc._search_entries(queries[-1], set())
                    cold = (time.perf_counter() - cold_start) * 1000
                    novel, repeated = [], []
                    for _ in range(7):
                        for query in queries:
                            nc.SEARCH_QUERY_CACHE.clear()
                            start = time.perf_counter()
                            nc._search_entries(query, set())
                            novel.append((time.perf_counter() - start) * 1000)
                            start = time.perf_counter()
                            nc._search_entries(query, set())
                            repeated.append((time.perf_counter() - start) * 1000)
                    row[name] = dict(cold_query_ms=cold, uncached_median_ms=statistics.median(novel),
                                     uncached_p95_ms=sorted(novel)[int(len(novel) * .95)],
                                     repeat_median_ms=statistics.median(repeated))
                report['cases'].append(row)
            bpy.data.node_groups.remove(tree)
    Path(args[1]).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('LANGUAGE_LATENCY_OK', len(report['cases']), flush=True)


if __name__ == '__main__':
    main()
