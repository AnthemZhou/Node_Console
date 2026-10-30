"""Compare the Add Shortcut modal action against 1.4.2 with synthetic settings."""
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
from zipfile import ZipFile

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from test_shortcut_save import console, load


def main():
    seed = json.loads((ROOT / 'node_console_builtin_cache.json').read_text())['trees']
    data = {'search_index_cache': {f'version-{i}-{tree}': entries for i in range(6)
                                   for tree, entries in seed.items()},
            'favorites': ['kept'], 'usage': {'kept': 42}, 'future': {'keep': [1, 2]},
            'shortcuts': [], 'favorite_meta': {}, 'favorite_tree_meta': {}, 'shortcut_tree_meta': {}}
    content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    report = {'blender': bpy.app.version_string, 'settings_bytes': len(content.encode()),
              'repeats': 15, 'measurements': {}}
    with tempfile.TemporaryDirectory(prefix='nc-shortcut-benchmark-') as directory:
        root = Path(directory)
        with ZipFile(ROOT / 'Node_Console_1.4.2.zip') as archive:
            archive.extractall(root)
        snapshots = []
        for label, source in [('before', root / 'Node_Console'), ('after', ROOT)]:
            path = root / (label + '.json')
            nc = load('NCShortcutBenchmark_' + label, source, path)
            samples = []
            for _ in range(16):
                path.write_text(content, encoding='utf-8')
                nc.SETTINGS_STORE.clear()
                nc._load_settings()
                op, context, event = console(nc)
                start = time.perf_counter()
                assert op.modal(context, event) == {'RUNNING_MODAL'}
                samples.append((time.perf_counter() - start) * 1000)
                assert op._query == '' and op._shortcuts == ['test:shortcut']
            snapshots.append(nc._load_settings())
            report['measurements'][label] = {'median_ms': round(statistics.median(samples[1:]), 3),
                                              'max_ms': round(max(samples[1:]), 3)}
        assert snapshots[0] == snapshots[1], 'Persisted settings changed'
        report['settings_parity'] = True
    Path(sys.argv[sys.argv.index('--') + 1]).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
