"""Exercise menu identity, context, variants and assets in isolated Blender."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
spec = importlib.util.spec_from_file_location('NCGapTest', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
output = Path(sys.argv[sys.argv.index('--') + 1])
nc._settings_path = lambda: Path(os.environ['BLENDER_USER_CONFIG']) / 'gap-test.json'
nc._preferences = lambda: None
sentinel = dict(favorites=['N_ShaderNodeBsdfAnisotropic_Glossy_BSDF'],
                shortcuts=['preserved'], usage={'preserved': 42},
                preferences={'display_mode': 'ZH_EN'})
nc._write_settings(sentinel)
passed = []
nc._refresh_asset_index()

assert nc.node_menu_search.canonical_node_type('ShaderNodeBsdfGlossy') == 'ShaderNodeBsdfAnisotropic'
passed.append('legacy RNA alias canonicalized without changing entry IDs')

for tree_type in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
    tree = bpy.data.node_groups.new('Isolated gaps', tree_type)
    context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_type,
        shader_type='OBJECT', node_tree_sub_type='SCENE' if tree_type == 'CompositorNodeTree' else 'MODIFIER',
        id_from=None, cursor_location=(0, 0)), engine='BLENDER_EEVEE')
    nc._rebuild_search_entries(context)
    entries = list(nc.NODE_SEARCH_ENTRIES)
    paths = [(e.identifier, e.menu_paths, e.native_hidden) for e in entries]
    nc._rebuild_search_entries(context)
    assert paths == [(e.identifier, e.menu_paths, e.native_hidden) for e in nc.NODE_SEARCH_ENTRIES]
    passed.append(tree_type + ': cold/warm cache identity and paths')
    experimental = bpy.context.preferences.experimental
    if tree_type == 'GeometryNodeTree' and hasattr(experimental, 'use_geometry_bundle'):
        original = experimental.use_geometry_bundle
        try:
            for enabled in (False, True):
                experimental.use_geometry_bundle = enabled
                nc._rebuild_search_entries(context)
                for query in ('Get Geometry Bundle', 'Set Geometry Bundle'):
                    assert any(e.english == query for e in nc._search_entries(query, set())) == enabled
        finally:
            experimental.use_geometry_bundle = original
            nc._rebuild_search_entries(context)
        passed.append('5.1 experimental Geometry Bundle follows official feature switch')
    if tree_type == 'ShaderNodeTree':
        by_id = {e.identifier: e for e in entries}
        glossy = by_id['N_ShaderNodeBsdfAnisotropic_Glossy_BSDF']
        assert glossy.menu_paths and glossy in nc._search_entries('\u7740\u8272\u5668', set())
        node = nc._add_builtin_node(context, glossy)
        assert node.bl_idname == 'ShaderNodeBsdfAnisotropic'
        tree.nodes.remove(node)
        for e in (e for e in entries if e.node_type == 'ShaderNodeMapRange'):
            node = nc._add_builtin_node(context, e)
            assert node.data_type == dict(e.settings).get('data_type', 'FLOAT')
            tree.nodes.remove(node)
        if bpy.app.version >= (5, 2, 0):
            vector = next(e for e in entries if e.node_type == 'ShaderNodeMapRange'
                          and dict(e.settings).get('data_type') == 'FLOAT_VECTOR')
            assert vector in nc._search_entries('map range', set())
            assert nc._search_entries('\u6620\u5c04\u8303\u56f4', set())[0] == vector
        assert nc._search_entries('\u8f93\u51fa', set())[0].node_type == 'ShaderNodeOutputAOV'
        passed.append('Shader: Glossy / output paths and Map Range variants create correctly')

        menu = bpy.types.NODE_MT_category_shader_output
        invoked = []
        def untrusted_menu(self, context):
            invoked.append(True)
            raise AssertionError('third-party callback must not execute')
        menu.append(untrusted_menu)
        try:
            captured, errors = nc.node_menu_search.collect(context, nc.node_registry.official_chinese_label)
            assert not errors and ('ShaderNodeOutputAOV', ()) in captured and not invoked
        finally:
            menu.remove(untrusted_menu)
        passed.append('wrapped official menus retained; appended add-on callback not executed')

        for engine, shader, owner in [('BLENDER_EEVEE', 'WORLD', None), ('CYCLES', 'OBJECT', bpy.context.object),
                                     ('CYCLES', 'OBJECT', SimpleNamespace(type='LIGHT'))]:
            context.engine = engine
            context.space_data.shader_type = shader
            context.space_data.id_from = owner
            nc._rebuild_search_entries(context)
            for query in ('shader', '\u7740\u8272\u5668', 'output', '\u8f93\u51fa', 'background'):
                result = nc._search_entries(query, set())
                assert all(not e.native_hidden for e in result)
            output_nodes = {e.node_type for e in nc._search_entries('output', set())}
            if shader == 'WORLD':
                assert 'ShaderNodeOutputWorld' in output_nodes and 'ShaderNodeOutputMaterial' not in output_nodes
                assert any(e.node_type == 'ShaderNodeBackground' for e in nc._search_entries('background', set()))
            else:
                assert not nc._search_entries('background', set())
                assert 'ShaderNodeOutputLight' in output_nodes
                # 5.1's official menu allows material output for all OBJECT
                # owners; 5.2 narrows it to non-light owners.
                material_expected = bpy.app.version < (5, 2, 0) or owner.type != 'LIGHT'
                assert ('ShaderNodeOutputMaterial' in output_nodes) == material_expected
            passed.append(f'Shader context: {engine}/{shader}/{getattr(owner, "type", None)}')

    if tree_type == 'CompositorNodeTree':
        assert nc._search_entries('\u5408\u6210', set())[0].node_type == 'CompositorNodeZcombine'
        assert all(not p[0].startswith('Compositing') for e in entries if e.kind == 'ASSET' for p in e.menu_paths)
        passed.append('Compositor assets omit editor root; Depth Combine ranks first')

    if tree_type == 'GeometryNodeTree' and bpy.app.version >= (5, 2, 0):
        assert not any(e.node_type == 'GeometryNodeToolMousePosition' for e in nc._search_entries('mouse', set()))
        modifier_key = nc._search_index_cache_key(context)
        context.space_data.node_tree_sub_type = 'TOOL'
        nc._rebuild_search_entries(context)
        assert nc._search_index_cache_key(context) != modifier_key
        assert any(e.node_type == 'GeometryNodeToolMousePosition' for e in nc._search_entries('mouse', set()))
        context.space_data.node_tree_sub_type = 'MODIFIER'
        nc._rebuild_search_entries(context)
        passed.append('Geometry tool-only nodes follow live official menu conditions')
        action = next(e for e in entries if e.node_type == 'node.add_typed_bundle')
        assert action.kind == 'ACTION' and action in nc._search_entries('bundle', set())
        area = bpy.context.window.screen.areas[0]
        original_type = area.type
        try:
            area.type = 'NODE_EDITOR'
            area.spaces.active.tree_type = tree_type
            area.spaces.active.pin = True
            area.spaces.active.node_tree = tree
            with bpy.context.temp_override(area=area):
                node = nc._add_menu_action(bpy.context, action)
                assert node.bl_idname == 'NodeCombineBundle'
                assert any(item.name == 'Type' and item.socket_type == 'STRING' for item in node.bundle_items)
                tree.nodes.remove(node)
        finally:
            area.type = original_type
        passed.append('Typed Bundle uses native operator and creates STRING Type item')
    bpy.data.node_groups.remove(tree)

assets = nc._load_asset_index()
assert assets and any(e['catalog_path'] for e in assets)
old = dict(path=assets[0]['path'], name='Legacy Asset', category='Geometry Nodes > Simulation')
with patch.object(nc, '_settings_value', return_value=[old, ['old.blend', 'Old tuple']]):
    parsed = nc._load_asset_index()
    assert nc._asset_search_catalog(parsed[0]) == 'Geometry Nodes/Simulation'
    assert len(parsed) == 2
new = dict(old, menu_catalog='Geometry Nodes-Simulation', catalog_path='Geometry Nodes/Simulation')
with patch.object(nc, '_settings_value', return_value=[new]):
    assert nc._load_asset_index()[0]['catalog_path'] == new['catalog_path']
passed.append('asset loader preserves catalogs and accepts historical snapshots')
assert all(nc._load_settings()[k] == v for k, v in sentinel.items())
passed.append('favorites, usage, shortcuts and preferences unchanged')
report = dict(version=bpy.app.version_string, passed=passed)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
