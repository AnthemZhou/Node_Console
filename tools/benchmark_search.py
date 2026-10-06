"""Compare local search behavior and timings against the published 1.2.1 ZIP."""
import cProfile
import importlib.util
import io
import json
import pstats
import statistics
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ('', 'm', 'ma', 'math', 'line', 'add', 'join', 'inst', 'instance',
           'shili', 'shilihua', 'slhyds', 'shange', 'zhage', 'noise', 'zao bo',
           '噪波', '随机', '矢量', 'vector math', 'VECTOR MATH', 'geometry',
           '颜色', 'yanse', 'filter', '滤镜', 'kuang', 'Frame', 'set',
           'qzx', 'zzzzmissing', 'String to Curves', 'stringtocurves')


def load(name, root, settings):
    spec = importlib.util.spec_from_file_location(name, root / '__init__.py',
                                                submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module._settings_path = lambda: settings
    module._preferences = lambda: None
    return module


def elapsed(call):
    started = time.perf_counter()
    value = call()
    return (time.perf_counter() - started) * 1000, value


def main():
    output = Path(sys.argv[sys.argv.index('--') + 1])
    report = {'version': bpy.app.version_string, 'trees': {}, 'failures': []}
    with tempfile.TemporaryDirectory(prefix='nc-search-benchmark-') as directory:
        temp = Path(directory)
        with zipfile.ZipFile(ROOT / 'Node_Console_1.2.1.zip') as archive:
            archive.extractall(temp)
        baseline = load('NCPerfBaseline', temp / 'Node_Console', temp / 'old.json')
        current = load('NCPerfCurrent', ROOT, temp / 'new.json')
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Search benchmark', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(
                edit_tree=tree, tree_type=tree_id, cursor_location=(0, 0)))
            results = {}
            for name, module in (('baseline', baseline), ('current', current)):
                cold, _ = elapsed(lambda: module._rebuild_search_entries(context))
                warm = [elapsed(lambda: module._rebuild_search_entries(context))[0] for _ in range(3)]
                times = []
                snapshots = []
                favorite = {e.identifier for e in module.NODE_SEARCH_ENTRIES[::13]}
                for favorites in (set(), favorite):
                    for query in QUERIES:
                        duration, found = elapsed(lambda: module._search_entries(query, favorites))
                        times.append(duration)
                        snapshots.append([e.identifier for e in found])
                results[name] = snapshots
                report['trees'].setdefault(tree_id, {})[name] = {
                    'entries': len(module.NODE_SEARCH_ENTRIES), 'cold_build_ms': cold,
                    'warm_build_ms': statistics.median(warm),
                    'search_median_ms': statistics.median(times),
                    'search_max_ms': max(times), 'queries': len(times),
                }
            if results['baseline'] != results['current']:
                report['failures'].append([tree_id, 'search result/order mismatch'])
            # Also compare names, pinyin, initials and prefixes across the index.
            queries = set()
            for entry in baseline.NODE_SEARCH_ENTRIES:
                for text in (entry.english, entry.chinese, entry.leaf_pinyin_compact,
                             entry.leaf_pinyin_initials):
                    queries.update((text, text[:3]))
            queries.discard('')
            for query in sorted(queries):
                expected = [e.identifier for e in baseline._search_entries(query, set())]
                actual = [e.identifier for e in current._search_entries(query, set())]
                if actual != expected:
                    report['failures'].append([tree_id, query, 'generated query mismatch'])
            report['trees'][tree_id]['parity_queries'] = len(queries)
            print('BENCHMARK', tree_id, report['trees'][tree_id], flush=True)
            bpy.data.node_groups.remove(tree)
        profile = cProfile.Profile()
        profile.enable()
        for query in QUERIES:
            current._search_entries(query, set())
        profile.disable()
        stream = io.StringIO()
        pstats.Stats(profile, stream=stream).sort_stats('cumtime').print_stats(25)
        report['profile'] = stream.getvalue()
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(report['profile'])
        assert not report['failures'], report['failures'][:10]


if __name__ == '__main__':
    main()
