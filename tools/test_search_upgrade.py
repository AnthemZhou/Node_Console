"""Compare persistent search identities with a previous release in isolation."""
import importlib.util
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

ROOT = Path(__file__).resolve().parents[1]


def load(name, root, settings):
    spec = importlib.util.spec_from_file_location(
        name, root / '__init__.py', submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module._settings_path = lambda: settings
    module._preferences = lambda: None
    return module


def identity(entry):
    return (entry.kind, entry.node_type, entry.asset_name, entry.asset_path,
            repr(entry.settings), entry.identifier)


def main():
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(
        os.environ['BLENDER_USER_CONFIG']).resolve()
    bpy.context.preferences.use_preferences_save = False
    args = sys.argv[sys.argv.index('--') + 1:]
    report = {'blender': bpy.app.version_string, 'trees': {}, 'failures': []}
    with tempfile.TemporaryDirectory(prefix='nc-upgrade-') as directory:
        root = Path(directory)
        with ZipFile(args[0]) as archive:
            archive.extractall(root)
        settings = root / 'settings.json'
        old = load('NCPreviousSearch', root / 'Node_Console', settings)
        new = load('NCNextSearch', ROOT, settings)
        old._refresh_asset_index()
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Search upgrade', tree_id)
            group = bpy.data.node_groups.new('Persistent local group', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(
                edit_tree=tree, tree_type=tree_id, shader_type='OBJECT',
                id_from=bpy.context.object), engine='BLENDER_EEVEE')
            try:
                old._rebuild_search_entries(context)
                previous = {identity(entry) for entry in old.NODE_SEARCH_ENTRIES}
                identifiers = [entry.identifier for entry in old.NODE_SEARCH_ENTRIES]
                sentinel = {'favorites': identifiers[::7], 'shortcuts': identifiers[::13],
                            'usage': {key: index for index, key in enumerate(identifiers)},
                            'custom_setting': {'value': 'preserved'}}
                data = old._load_settings()
                data.update(sentinel)
                old._write_settings(data)
                new._rebuild_search_entries(context)
                current = {identity(entry) for entry in new.NODE_SEARCH_ENTRIES}
                assert previous == current, (tree_id, previous - current, current - previous)
                assert all(new._load_settings()[key] == value for key, value in sentinel.items())
                assert all(key in new.NODE_ENTRY_BY_ID for key in identifiers)
                report['trees'][tree_id] = {'preserved_identities': len(current)}
                queries = ('mesh', 'add', 'line', 'instance', 'nt', 'niose',
                           '\u566a\u6ce2', '\u6a21\u7cca', 'shili', 'zbwl')
                for name, module in (('previous', old), ('current', new)):
                    for query in queries:
                        module._search_entries(query, set())
                    timings = []
                    for _ in range(3):
                        for query in queries:
                            start = time.perf_counter()
                            module._search_entries(query, set())
                            timings.append((time.perf_counter() - start) * 1000)
                    report['trees'][tree_id][name + '_median_ms'] = statistics.median(timings)
            finally:
                bpy.data.node_groups.remove(group)
                bpy.data.node_groups.remove(tree)
    Path(args[1]).write_text(json.dumps(report, indent=2))
    print('SEARCH_UPGRADE_REGRESSION', report, flush=True)


if __name__ == '__main__':
    main()
