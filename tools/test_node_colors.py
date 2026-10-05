"""Factory-Blender color regression against the previous release, without user settings."""
import importlib.util
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
TAGS = {
    'ATTRIBUTE': 'attribute', 'INPUT': 'input', 'COLOR': 'color',
    'CONVERTER': 'converter', 'TEXTURE': 'texture', 'GEOMETRY': 'geometry',
    'VECTOR': 'vector', 'FILTER': 'compositor_filter', 'MATTE': 'compositor_mask',
    'DISTORT': 'compositor_distort', 'SHADER': 'shader', 'SCRIPT': 'script',
}
FIXES = {
    'GeometryNodeCurveLength': 'geometry',
    'GeometryNodeStringToCurves': 'geometry',
    'ShaderNodeOutputLight': 'special_output',
    'ShaderNodeOutputLineStyle': 'special_output',
}


def load(name, root, settings):
    spec = importlib.util.spec_from_file_location(name, root / '__init__.py',
                                                submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module._settings_path = lambda: settings
    module._preferences = lambda: None
    return module


def color(module, entry):
    value = module._entry_base_type_color(entry)
    return next(key for key, rgba in module.NODE_TYPE_COLORS.items() if rgba == value)


def main():
    report = {'version': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode(),
              'nodes': [], 'assets': [], 'failures': []}
    with tempfile.TemporaryDirectory(prefix='nc-colors-') as directory:
        temp = Path(directory)
        with zipfile.ZipFile(ROOT / 'Node_Console_1.2.0.zip') as archive:
            archive.extractall(temp)
        old = load('NCColorBaseline', temp / 'Node_Console', temp / 'old.json')
        nc = load('NCColorCurrent', ROOT, temp / 'current.json')
        assert nc._snippet_category_color_type('SHADER') == 'shader'
        assert nc._asset_category_from_color_tag('FILTER') == 'Filter'
        records = []
        for location in nc._built_in_asset_node_directories():
            records.extend(nc._scan_asset_node_groups([location]))
        for module in (old, nc):
            module._save_asset_index(records)
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Color regression', tree_id)
            context = SimpleNamespace(space_data=SimpleNamespace(
                edit_tree=tree, tree_type=tree_id, cursor_location=(0, 0)))
            old._rebuild_search_entries(context)
            baseline = dict(old.NODE_ENTRY_BY_ID)
            nc._rebuild_search_entries(context)
            entries = list(nc.NODE_SEARCH_ENTRIES)
            assert set(baseline) == set(nc.NODE_ENTRY_BY_ID), tree_id
            for entry in entries:
                previous = color(old, baseline[entry.identifier])
                actual = color(nc, entry)
                expected = previous
                node = None
                try:
                    if entry.kind == 'NODE':
                        node = nc._add_builtin_node(context, entry)
                        tag = node.color_tag
                        if tag in {'SHADER', 'SCRIPT'}:
                            expected = TAGS[tag]
                        expected = FIXES.get(entry.node_type, expected)
                        report['nodes'].append({'tree': tree_id, 'id': entry.node_type,
                            'name': entry.english, 'tag': tag, 'before': previous,
                            'after': actual, 'expected': expected})
                    elif entry.kind == 'ASSET' and entry.asset_path:
                        node = nc._add_asset_node(context, entry)
                        tag = node.node_tree.color_tag
                        expected = TAGS.get(tag, previous)
                        report['assets'].append({'tree': tree_id, 'name': entry.english,
                            'tag': tag, 'before': previous, 'after': actual, 'expected': expected})
                    assert actual == expected, (entry.english, previous, actual, expected)
                except Exception as error:
                    report['failures'].append([tree_id, entry.identifier, str(error)])
                finally:
                    if node:
                        group = node.node_tree if entry.kind == 'ASSET' else None
                        tree.nodes.remove(node)
                        if group:
                            bpy.data.node_groups.remove(group)
            # A warm cache must produce the same colors as the initial build.
            before = {e.identifier: color(nc, e) for e in entries}
            nc._rebuild_search_entries(context)
            after = {e.identifier: color(nc, e) for e in nc.NODE_SEARCH_ENTRIES}
            # Appended asset dependencies can introduce additional local groups.
            assert all(after.get(key) == value for key, value in before.items())
            bpy.data.node_groups.remove(tree)
        output = Path(sys.argv[sys.argv.index('--') + 1])
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print('COLOR_REGRESSION', report['version'], len(report['nodes']), len(report['assets']),
              'changed', sum(r['before'] != r['after'] for r in report['nodes'] + report['assets']),
              'failures', report['failures'])
        assert not report['failures']


if __name__ == '__main__':
    main()
