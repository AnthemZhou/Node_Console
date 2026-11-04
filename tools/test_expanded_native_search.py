"""Replay independently captured native search rows against the actual index."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from analyze_search_audit import compare

assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
parser.add_argument('--fixture', type=Path, default=ROOT / 'tools/fixtures/native_search_expanded_5_2_2.json')
parser.add_argument('--multilingual', action='store_true')
parser.add_argument('--english-only', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
fixture = json.loads(args.fixture.read_text())
assert bpy.app.version_string == fixture['blender'] and bpy.app.build_hash.decode() == fixture['build'], 'Use the audited Blender build'
spec = importlib.util.spec_from_file_location('NCExpandedTest', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._settings_path = lambda: Path(os.environ['BLENDER_USER_CONFIG']) / 'expanded-test.json'
nc._preferences = lambda: None
if args.english_only:
    assert not args.multilingual
    nc._search_language = lambda: 'en_US'
    fixture['cases'] = [case for case in fixture['cases']
                        if case['language'] == 'en_US' and case['group'] in {'baseline', 'context'}]
nc._refresh_asset_index()
last_context = None
tree = None
results = []
failures = []
try:
    for sample in fixture['cases']:
        key = tuple(sample[k] for k in ('tree', 'engine', 'shader'))
        if args.multilingual:
            key += (sample['language'],)
        if key != last_context:
            if tree:
                bpy.data.node_groups.remove(tree)
            tree = bpy.data.node_groups.new('Expanded replay', sample['tree'])
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=sample['tree'],
                shader_type=sample['shader'], node_tree_sub_type='SCENE' if sample['tree'] == 'CompositorNodeTree' else 'MODIFIER',
                id_from=None), engine=sample['engine'])
            if args.multilingual:
                nc._search_language = lambda: sample['language']
                nc._clear_search_caches()
            nc._rebuild_search_entries(context)
            last_context = key
        bpy.context.preferences.view.language = sample['language']
        found = nc._search_entries(sample['query'], set())
        portable = ['ASSET:' + e.english if e.kind == 'ASSET' else 'ENTRY:' + e.identifier for e in found]
        metrics = compare(sample['native'], portable)
        results.append(dict(sample, actual=portable[:10], **metrics))
        if sample['group'] in {'baseline', 'context'}:
            if metrics['missing'] or (sample['baseline_first'] and not metrics['first']) or (sample['baseline_exact'] and not metrics['visible_exact']):
                failures.append([sample['tree'], sample['query'], sample['native'], portable[:10]])
        elif bool(found) != sample['extension_has_results']:
            failures.append([sample['tree'], sample['query'], 'extension availability changed'])
finally:
    if tree:
        bpy.data.node_groups.remove(tree)
comparable = [s for s in results if s['group'] in {'baseline', 'context'}]
report = dict(version=bpy.app.version_string, cases=len(results), comparable=len(comparable),
              first=sum(s['first'] for s in comparable), exact=sum(s['visible_exact'] for s in comparable),
              positions=sum(len(s['native']) for s in comparable),
              position_matches=sum(s['position_matches'] for s in comparable),
              missing_cases=sum(bool(s['missing']) for s in comparable), failures=failures)
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
assert not failures, 'Expanded native-search regression; see report'
