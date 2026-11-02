"""Measure cold and warmed input matching in an isolated Blender process."""
import cProfile
import importlib.util
import io
import json
import os
from pathlib import Path
import pstats
import statistics
import sys
import time
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
spec = importlib.util.spec_from_file_location('NCInputProfile', ROOT / '__init__.py',
                                            submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._settings_path = lambda: Path(os.environ['BLENDER_USER_CONFIG']) / 'settings.json'
nc._preferences = lambda: None
nc._refresh_asset_index()
queries = ('\u8bbe', '\u8bbe\u7f6e', 'she zhi', 'shezhi', 'sz', '\u96c6\u5408',
           '\u566a\u6ce2', '\u5b9e\u4f8b', '\u6a21\u7cca', 'add', 'line', 'nt',
           'niose', 'set position', 'shili', 'zbwl', 'random value', 'zzzzmissing')
report = {'version': bpy.app.version_string, 'trees': {}}
for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
    tree = bpy.data.node_groups.new('Input profile', tree_id)
    context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id), engine='BLENDER_EEVEE')
    nc._rebuild_search_entries(context)
    start = time.perf_counter()
    result = nc._search_entries('\u8bbe\u7f6e', set())
    cold = (time.perf_counter() - start) * 1000
    snapshots = {q: [e.identifier for e in nc._search_entries(q, set())] for q in queries}
    timings = {}
    for query in queries:
        samples = []
        for _ in range(10):
            start = time.perf_counter()
            nc._search_entries(query, set())
            samples.append((time.perf_counter() - start) * 1000)
        timings[query] = statistics.median(samples)
    profiler = cProfile.Profile()
    profiler.runcall(nc._search_entries, '\u8bbe\u7f6e', set())
    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats('cumtime').print_stats(22)
    report['trees'][tree_id] = dict(cold_ms=cold, warm_ms=timings,
        chinese_set=[dict(id=e.identifier, english=e.english, chinese=e.chinese,
                         paths=e.menu_paths) for e in result],
        snapshots=snapshots, profile=stream.getvalue())
    print(tree_id, 'cold', round(cold, 3), 'warm', round(timings['\u8bbe\u7f6e'], 3), flush=True)
    print(stream.getvalue(), flush=True)
    bpy.data.node_groups.remove(tree)
Path(sys.argv[sys.argv.index('--') + 1]).write_text(json.dumps(report, ensure_ascii=False, indent=2))
