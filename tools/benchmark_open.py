"""Profile first-open preparation in an isolated Blender process."""
import cProfile
import importlib.util
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

import bpy

ROOT = Path(__file__).resolve().parents[1]


def load(name, root, settings):
    spec = importlib.util.spec_from_file_location(
        name, root / '__init__.py', submodule_search_locations=[str(root)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[name] = nc
    spec.loader.exec_module(nc)
    nc._settings_path = lambda: settings
    nc._preferences = lambda: None
    return nc


def main():
    assert bpy.utils.user_resource('CONFIG') == os.environ['BLENDER_USER_CONFIG']
    bpy.context.preferences.use_preferences_save = False
    args = sys.argv[sys.argv.index('--') + 1:]
    output = Path(args[0])
    root = Path(args[1]) if len(args) > 1 else ROOT
    report = {'blender': bpy.app.version_string, 'trees': {}}
    with tempfile.TemporaryDirectory(prefix='nc-open-') as directory:
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            name = 'NCOpen' + tree_id
            settings = Path(directory) / (tree_id + '.json')
            nc = load(name, root, settings)
            tree = bpy.data.node_groups.new('Open benchmark', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(
                edit_tree=tree, tree_type=tree_id, cursor_location=(0, 0)))
            timings = []
            try:
                for _ in range(6):
                    start = time.perf_counter()
                    nc._rebuild_search_entries(context)
                    timings.append((time.perf_counter() - start) * 1000)
                # Fresh module state, with only the persisted index available.
                disk_times = []
                for index in range(3):
                    nc = load(name + 'Disk' + str(index), root, settings)
                    start = time.perf_counter()
                    nc._rebuild_search_entries(context)
                    disk_times.append((time.perf_counter() - start) * 1000)
                nc = load(name + 'Profile', root, settings)
                profile = cProfile.Profile()
                start = time.perf_counter()
                profile.runcall(nc._rebuild_search_entries, context)
                disk_ms = (time.perf_counter() - start) * 1000
                stream = io.StringIO()
                pstats.Stats(profile, stream=stream).sort_stats('cumtime').print_stats(22)
                report['trees'][tree_id] = {
                    'first_ms': timings[0], 'warm_ms': statistics.median(timings[1:]),
                    'disk_ms': statistics.median(disk_times),
                    'disk_profiled_ms': disk_ms, 'entries': len(nc.NODE_SEARCH_ENTRIES),
                    'profile': stream.getvalue(),
                }
                print(tree_id, {k: v for k, v in report['trees'][tree_id].items() if k != 'profile'}, flush=True)
            finally:
                bpy.data.node_groups.remove(tree)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
