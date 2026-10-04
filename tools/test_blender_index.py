"""Isolated search/create regression test. No user settings are read or written."""
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('Node_Console', ROOT / '__init__.py',
                                             submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)

CANDIDATES = (
    'Get Geometry Bundle', 'Set Geometry Bundle', 'Field to List', 'Closure to List',
    'List Length', 'Get List Item', 'Filter List', 'Sort List', 'Collection Children',
    'Sample Sound Frequencies', 'Merge Points', 'Cluster by Distance', 'Cluster by Connected',
    'Mesh Bevel', 'Rename Attribute', 'Get Attribute Names', 'Transfer Attributes',
    'Set NURBS Order', 'Set NURBS Weight', 'Instance Reference', 'Get Geometry Component',
    'XPBD Solver', 'Trim String', 'Reverse String', 'Set String Case', 'Split String',
    'Blank Image', 'String To Image', 'Implicit Conversion', 'Menu', 'Font', 'Scene Time',
    'Boolean', 'Integer', 'Vector', 'Active Camera', 'Camera Info', 'Object', 'Object Info',
    'Warning', 'Integer Vector', 'Get Nested Bundle Paths', 'Tag Filter',
)


def main():
    report = {'version': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode(),
              'trees': {}, 'failures': [], 'candidates': {}, 'assets': []}
    with tempfile.TemporaryDirectory(prefix='node-console-test-') as directory:
        temp = Path(directory)
        nc._settings_path = lambda: temp / 'settings.json'
        sentinel = {'favorites': ['saved-id'], 'usage': {'saved-id': 42},
                    'preferences': {'display_mode': 'ZH_EN'}, 'shortcuts': ['saved-id']}
        nc._write_settings(sentinel)
        before_language = bpy.context.preferences.view.language
        for tree_type in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Index test', tree_type)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_type, cursor_location=(0, 0)))
            started = time.monotonic()
            nc._rebuild_search_entries(context)
            build_seconds = time.monotonic() - started
            entries = list(nc.NODE_SEARCH_ENTRIES)
            capabilities = nc.node_registry.inventory(tree)
            types = {e.node_type for e in entries if e.kind == 'NODE'}
            missing = sorted(set(capabilities) - types)
            if missing:
                report['failures'].append([tree_type, 'missing registered types', missing])
            for entry in entries:
                if entry.kind != 'NODE':
                    continue
                try:
                    node = nc._add_builtin_node(context, entry)
                    assert node.bl_idname == entry.node_type
                    for name, value in entry.settings:
                        if name.startswith('inputs[') and name.endswith('].default_value'):
                            socket_name = nc.ast.literal_eval(name[7:-15])
                            assert node.inputs[socket_name].default_value == value
                        elif name != 'visible_output':
                            assert getattr(node, name) == value, (entry.english, name, value)
                    tree.nodes.remove(node)
                except Exception as error:
                    report['failures'].append([tree_type, entry.english, str(error)])
                for query in (entry.english, entry.chinese, entry.leaf_pinyin_compact, entry.leaf_pinyin_initials):
                    if query and nc._score_entry(entry, query, set()) is None:
                        report['failures'].append([tree_type, 'unsearchable', entry.english, query])
            for label in CANDIDATES:
                matches = [e for e in entries if e.kind == 'NODE' and e.english == label]
                if not matches:
                    continue
                entry = matches[0]
                queries = [label, label.upper(), label.replace(' ', ''), entry.chinese,
                           entry.leaf_pinyin_compact, entry.leaf_pinyin_initials]
                for query in queries:
                    if query and not any(e.node_type == entry.node_type for e in nc._search_entries(query, set())):
                        report['failures'].append([tree_type, 'search result', label, query])
                report['candidates'].setdefault(label, {})[tree_type] = {
                    'id': entry.node_type, 'chinese': entry.chinese,
                    'pinyin': entry.leaf_pinyin_compact, 'initials': entry.leaf_pinyin_initials,
                    'category': entry.category,
                }
            for query, expected in (('math', 'ShaderNodeMath'), ('join', 'GeometryNodeJoinGeometry'),
                                    ('inst', 'GeometryNodeInstanceOnPoints'), ('line', 'GeometryNodeMeshLine')):
                if expected in types:
                    found = nc._search_entries(query, set())
                    if not found or found[0].node_type != expected:
                        report['failures'].append([tree_type, 'ranking', query, [e.english for e in found[:3]]])
            for mode, expected_label in (('ENGLISH', 'Math'), ('CHINESE', '运算'),
                                         ('ENGLISH_CHINESE', 'Math / 运算'), ('CHINESE_ENGLISH', '运算 / Math')):
                original = nc._display_mode
                nc._display_mode = lambda: mode
                sample = nc._entry_label('Math', '运算')
                assert sample == expected_label, (mode, sample)
                nc._display_mode = original
            report['trees'][tree_type] = {'entries': len(entries), 'node_types': len(types),
                                         'node_ids': sorted(types),
                                         'build_seconds': round(build_seconds, 3),
                                         'seconds': round(time.monotonic() - started, 3)}
            # Warm disk-cache rebuild must preserve the same IDs and capabilities.
            ids = {e.identifier for e in entries}
            nc._rebuild_search_entries(context)
            if ids != {e.identifier for e in nc.NODE_SEARCH_ENTRIES}:
                report['failures'].append([tree_type, 'cache identity changed'])
            menu_types = {row[0] for row in nc._iter_menu_entries(context)}
            assert not ((menu_types & set(capabilities)) - types)
            report['trees'][tree_type]['menu_types_checked'] = len(menu_types & set(capabilities))
            baseline = [(e.identifier, e.english, e.chinese) for e in nc.NODE_SEARCH_ENTRIES]
            for language in ('en_US', 'zh_HANS'):
                # Only the isolated factory-startup test changes language.
                bpy.context.preferences.view.language = language
                nc._rebuild_search_entries(context)
                assert [(e.identifier, e.english, e.chinese) for e in nc.NODE_SEARCH_ENTRIES] == baseline
                assert bpy.context.preferences.view.language == language
            bpy.context.preferences.view.language = before_language
            # Exercise the non-macOS transliteration path on this machine too.
            original_system = nc._system_pinyin
            nc._system_pinyin = lambda text: ''
            nc.PINYIN_PROFILE_CACHE.clear()
            nc.PINYIN_TEXT_CACHE.clear()
            for entry in entries:
                if entry.english in CANDIDATES:
                    fallback = nc.replace(entry, leaf_pinyin_compact='', root_pinyin_compact='')
                    for query in (fallback.leaf_pinyin_compact, fallback.leaf_pinyin_initials):
                        if query and nc._score_entry(fallback, query, set()) is None:
                            report['failures'].append([tree_type, 'fallback pinyin', entry.english, query])
            for text, expected in (('重命名属性', 'chong ming ming shu xing'),
                                   ('过滤列表', 'guo lv lie biao'), ('频率', 'pin lv'),
                                   ('设置 NURBS 阶数', 'she zhi nurbs jie shu')):
                assert nc._source_pinyin(text) == expected, (text, nc._source_pinyin(text))
            nc._system_pinyin = original_system
            nc.PINYIN_PROFILE_CACHE.clear()
            nc.PINYIN_TEXT_CACHE.clear()
            bpy.data.node_groups.remove(tree)
        assert bpy.context.preferences.view.language == before_language
        saved = nc._load_settings()
        assert all(saved[k] == v for k, v in sentinel.items())
        report['preserves_settings_and_language'] = True
        # Asset scanner uses only local files. Two libraries with identical group
        # names must retain source names and load distinct datablocks.
        for index in (1, 2):
            group = bpy.data.node_groups.new('Same Name', 'GeometryNodeTree')
            group.asset_mark()
            group['source_number'] = index
            bpy.data.libraries.write(str(temp / f'library{index}.blend'), {group})
            bpy.data.node_groups.remove(group)
        loaded = []
        collision_records = []
        for index in (1, 2):
            path = temp / f'library{index}.blend'
            records = nc._read_asset_node_groups(path)
            assert records[0]['name'] == 'Same Name'
            collision_records.extend(records)
            entry = nc.NodeSearchEntry('asset', 'Asset', 'Same Name', 'Same Name', 'Same Name', '',
                                       'ASSET', asset_path=str(path), asset_name='Same Name')
            group = nc._load_asset_node_group(entry)
            assert group['source_number'] == index
            loaded.append(group)
        assert loaded[0] != loaded[1]
        library = bpy.context.preferences.filepaths.asset_libraries.new(name='NC test library', directory=str(temp))
        assert temp in nc._external_asset_node_directories()
        bpy.context.preferences.filepaths.asset_libraries.remove(library)
        unavailable = nc.replace(entry, asset_path=str(temp / 'not-downloaded.blend'))
        assert not nc._entry_available_in_current_blender(None, unavailable)
        nc._save_asset_index(collision_records)
        tree = bpy.data.node_groups.new('Collision test', 'GeometryNodeTree')
        context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree.bl_idname))
        nc._rebuild_search_entries(context)
        same_name = [e for e in nc.NODE_SEARCH_ENTRIES if e.kind == 'ASSET' and e.asset_name == 'Same Name']
        assert len(same_name) == 3  # Two libraries and the existing local datablock.
        assert len({e.identifier for e in same_name}) == 3
        bpy.data.node_groups.remove(tree)
        for group in loaded:
            bpy.data.node_groups.remove(group)
        report['asset_same_name_isolation'] = True
        for directory in nc._built_in_asset_node_directories():
            report['assets'].extend(nc._scan_asset_node_groups([directory]))
        nc._save_asset_index(report['assets'])
        for tree_type in report['trees']:
            tree = bpy.data.node_groups.new('Asset index test', tree_type)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_type, cursor_location=(0, 0)))
            nc._rebuild_search_entries(context)
            for record in report['assets']:
                if record['tree_type'] != tree_type:
                    continue
                matches = [e for e in nc.NODE_SEARCH_ENTRIES if e.kind == 'ASSET'
                           and (e.asset_path, e.asset_name) == (record['path'], record['name'])]
                assert len(matches) == 1, record
                for query in (matches[0].english, matches[0].chinese,
                              matches[0].leaf_pinyin_compact, matches[0].leaf_pinyin_initials, *matches[0].aliases):
                    if query:
                        assert nc._score_entry(matches[0], query, set()) is not None, (record['name'], query)
                node = nc._add_asset_node(context, matches[0])
                group = node.node_tree
                assert group and group.bl_idname == tree_type
                assert node.node_tree == group
                tree.nodes.remove(node)
                bpy.data.node_groups.remove(group)
            bpy.data.node_groups.remove(tree)
    output = Path(sys.argv[sys.argv.index('--') + 1])
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('RESULT', report['version'], report['trees'], 'failures:', len(report['failures']))
    for failure in report['failures'][:20]:
        print('FAIL', failure)
    if report['failures']:
        raise RuntimeError('Index regression failures; see report')


main()
