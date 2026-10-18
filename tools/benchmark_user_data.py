"""Compare user-data hot paths against 1.3.1, using synthetic temporary libraries."""
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace
from zipfile import ZipFile

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from test_preferences_ui import Layout


def load(name, root, directory):
    spec = importlib.util.spec_from_file_location(name, root / '__init__.py',
                                                submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module._settings_path = lambda: directory / 'settings.json'
    module._snippets_path = lambda: directory / 'snippets.json'
    module._preferences = lambda: None
    return module


def measure(call, repeats=15):
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(samples), 3)


def main():
    report = {'blender': bpy.app.version_string, 'baseline': '1.3.1', 'measurements': {}}
    with tempfile.TemporaryDirectory(prefix='nc-data-benchmark-') as directory:
        temp = Path(directory)
        with ZipFile(ROOT / 'Node_Console_1.3.1.zip') as archive:
            archive.extractall(temp)
        old = load('NCDataBaseline', temp / 'Node_Console', temp / 'old')
        new = load('NCDataCurrent', ROOT, temp / 'new')
        trees = []
        try:
            favorites, shortcuts, tree_meta = [], [], {}
            for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
                tree = bpy.data.node_groups.new('Data benchmark', tree_id)
                trees.append(tree)
                context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_id))
                new._rebuild_search_entries(context)
                entries = new.NODE_SEARCH_ENTRIES[::17]
                for entry in entries:
                    tree_meta.setdefault(entry.identifier, []).append(tree_id)
                    favorites.append(entry.identifier)
                    shortcuts.append(entry.identifier)
            data = new._load_settings()
            data.update(favorites=favorites, shortcuts=shortcuts,
                        favorite_tree_meta=tree_meta, shortcut_tree_meta=tree_meta,
                        usage={'preserved': 27}, future_field={'kept': True})
            geometry = trees[0]
            frame = geometry.nodes.new('NodeFrame')
            previous = None
            for index in range(12):
                node = geometry.nodes.new('ShaderNodeMath')
                node.parent = frame
                node.location = (index * 200, 0)
                node.inputs[1].default_value = index / 10
                if previous:
                    geometry.links.new(previous.outputs[0], node.inputs[0])
                previous = node
            payload = new._serialize_snippet_nodes(geometry, set(geometry.nodes), frame)
            snippets = [{'id': str(i), 'name': f'Noise texture 噪波 {i:03}',
                         'category': 'TEXTURE', 'tree_type': 'GeometryNodeTree',
                         'payload': payload} for i in range(200)]
            for module in (old, new):
                module._write_settings(data)
                module._save_snippets(snippets)
                # Both start from the same cached native entries and user data.
                module._rebuild_search_entries(SimpleNamespace(space_data=SimpleNamespace(
                    edit_tree=geometry, tree_type='GeometryNodeTree')))
            # Different add-on versions have different index keys; equalize the file size.
            common = old._load_settings()
            common['search_index_cache'].update(new._load_settings()['search_index_cache'])
            for module in (old, new):
                module._write_settings(common)

            results = {}
            for label, module in (('before', old), ('after', new)):
                prefs = SimpleNamespace(snippet_nodes_expanded=False)
                ui_context = SimpleNamespace(region=SimpleNamespace(width=1200))

                def draw_prefs():
                    prefs.layout = Layout()
                    module.ENS_AddonPreferences.draw(prefs, ui_context)

                def cold_snippets():
                    module._clear_search_caches()
                    if hasattr(module, 'SNIPPETS_STORE'):
                        module.SNIPPETS_STORE.clear()
                    module._search_snippets('zaobo', 'GeometryNodeTree', set())

                measurements = {
                    'favorites_and_shortcuts_ms': measure(lambda: (
                        module._load_favorites_for_tree('GeometryNodeTree'),
                        module._load_shortcuts_for_tree('GeometryNodeTree'))),
                    'preferences_collapsed_ms': measure(draw_prefs),
                    'snippet_query_ms': measure(lambda: module._search_snippets(
                        'zaobo', 'GeometryNodeTree', {'snippet:12'})),
                    'snippet_first_query_ms': measure(cold_snippets, repeats=5),
                }
                prefs.snippet_nodes_expanded = True
                measurements['preferences_expanded_ms'] = measure(draw_prefs)
                report['measurements'][label] = measurements
                results[label] = [[entry.identifier for entry in module._search_snippets(query, tree_id, favs)]
                                  for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree')
                                  for favs in (set(), {'snippet:12', 'snippet:7'})
                                  for query in ('', 'noise', 'Noise', 'texture', '噪波', 'zaobo', 'z b', 'zb', '019', 'missing')]
                preserved = module._load_settings()
                assert all(preserved[key] == data[key] for key in data if key != 'search_index_cache')
            assert results['before'] == results['after'], 'Snippet result/order changed'
            report.update(settings_bytes=new._settings_path().stat().st_size,
                          library_bytes=new._snippets_path().stat().st_size,
                          snippets=len(snippets), parity_checks=len(results['after']))
        finally:
            for tree in trees:
                bpy.data.node_groups.remove(tree)
    output = Path(sys.argv[sys.argv.index('--') + 1])
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
