"""5.3 public RNA/menu/search/color coverage; also exercises older-version gating."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]
# These identifiers were audited against the official 5.3.0 release runtime,
# not inferred from release-note titles. Shared types occur in multiple trees.
ADDITIONS = {
    'GeometryNodeTree': '''FunctionNodeGetVectorComponent GeometryNodeCombineList
        GeometryNodeConstructCurves GeometryNodeGeometryMaterials GeometryNodeGetGridNames
        GeometryNodeGreasePencilColor GeometryNodeGreasePencilDrawTime GeometryNodeGreasePencilFillID
        GeometryNodeGreasePencilOpacity GeometryNodeGreasePencilStrokeSoftness
        GeometryNodeGreasePencilStrokeVisibility GeometryNodeGridDeactivateVoxels
        GeometryNodeGridSolvePoisson GeometryNodeGridTopologyBoolean GeometryNodeImportSPZ
        GeometryNodeNURBSOrder GeometryNodeNURBSWeight GeometryNodePointsSetType
        GeometryNodeRasterizePoints NodeComment'''.split(),
    'ShaderNodeTree': '''FunctionNodeBooleanMath FunctionNodeFindInString FunctionNodeFormatString
        FunctionNodeGetVectorComponent FunctionNodeInputSpecialCharacters FunctionNodeInputString
        FunctionNodeIntegerMath FunctionNodeMatchString FunctionNodeReplaceString
        FunctionNodeReverseString FunctionNodeSetStringCase FunctionNodeSliceString
        FunctionNodeStringLength FunctionNodeStringToValue FunctionNodeTrimString FunctionNodeValueToString
        GeometryNodeIndexSwitch GeometryNodeSwitch GeometryNodeWarning NodeComment NodeEnableOutput
        ShaderNodeLightAccumulation ShaderNodeLightEvaluation ShaderNodeLightInfo
        ShaderNodeShadowRaycast'''.split(),
    'CompositorNodeTree': '''FunctionNodeBitMath FunctionNodeBooleanMath FunctionNodeCombineTransform
        FunctionNodeCompare FunctionNodeFloatToInt FunctionNodeGetVectorComponent FunctionNodeHashValue
        FunctionNodeIntegerMath FunctionNodeMatrixSVD FunctionNodeRandomValue FunctionNodeSeparateTransform
        GeometryNodeBoneInfo GeometryNodeImportText GeometryNodeIsViewport NodeCombineBundle NodeComment
        NodeGetBundleItem NodeSeparateBundle NodeStoreBundleItem'''.split(),
}
LIGHTS = {'ShaderNodeLightAccumulation', 'ShaderNodeLightEvaluation',
          'ShaderNodeLightInfo', 'ShaderNodeShadowRaycast'}


def main():
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
    bpy.context.preferences.use_preferences_save = False
    spec = importlib.util.spec_from_file_location('NC53Test', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    nc._preferences = lambda: None
    nc._settings_path = lambda: Path(os.environ['BLENDER_USER_CONFIG']) / '53-settings.json'
    sentinel = dict(favorites=['keep'], usage={'keep': 42}, shortcuts=['keep'], preferences={'display_mode': 'ZH_EN'})
    nc._write_settings(sentinel)
    ui_language = bpy.context.preferences.view.language
    nc._refresh_asset_index()
    report = dict(version=bpy.app.version_string, build_hash=bpy.app.build_hash.decode(),
                  trees={}, searches=0, creations=0, colors=0, checks=[])
    for tree_type, additions in ADDITIONS.items():
        tree = bpy.data.node_groups.new('5.3 audit', tree_type)
        context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_type,
            shader_type='OBJECT', node_tree_sub_type='SCENE' if tree_type == 'CompositorNodeTree' else 'MODIFIER',
            id_from=bpy.context.object, cursor_location=(0, 0)), engine='BLENDER_EEVEE')
        nc._rebuild_search_entries(context)
        entries = list(nc.NODE_SEARCH_ENTRIES)
        inventory = nc.node_registry.inventory(tree)
        assert not nc.node_registry.INTERNAL_NODE_TYPES.intersection(e.node_type for e in entries)
        public = {e.node_type for e in entries if e.kind == 'NODE' and not e.native_hidden}
        if bpy.app.version >= (5, 3, 0):
            assert set(additions) <= public, (tree_type, set(additions) - public)
        else:
            assert not set(additions).intersection(public), (tree_type, set(additions).intersection(public))
        paths, errors = nc.node_menu_search.collect(context, nc.node_registry.official_chinese_label)
        assert not errors, errors
        covered = {nc.node_menu_search.semantic_key(e.node_type, e.settings)
                   for e in entries if e.kind == 'NODE' and not e.native_hidden}
        expected = {key for key in paths if key[0] in additions}
        assert expected <= covered, (tree_type, expected - covered)
        tested = []
        for entry in entries:
            if entry.kind != 'NODE' or entry.node_type not in additions or entry.native_hidden:
                continue
            node = nc._add_builtin_node(context, entry)
            assert node.bl_idname == entry.node_type
            report['creations'] += 1
            tag = node.color_tag
            if entry.node_type == 'NodeComment':
                expected_color = nc.NODE_TYPE_COLORS['output']
            elif tag in nc.NODE_COLOR_TAG_TYPES:
                expected_color = nc.NODE_TYPE_COLORS[nc.NODE_COLOR_TAG_TYPES[tag]]
            else:
                expected_color = None
            if expected_color is not None:
                assert nc._entry_base_type_color(entry) == expected_color, (entry.english, tag)
                report['colors'] += 1
            tree.nodes.remove(node)
            for query in (entry.english.split(' > ')[-1], entry.chinese.split(' > ')[-1],
                          entry.leaf_pinyin_compact, entry.leaf_pinyin_initials):
                if query:
                    assert entry.identifier in {e.identifier for e in nc._search_entries(query, set())}, (entry.english, query)
                    report['searches'] += 1
            tested.append(dict(id=entry.node_type, name=entry.english, chinese=entry.chinese, tag=tag))
        report['trees'][tree_type] = dict(public_types=len(public), inventory_types=len(inventory),
                                         new_editor_memberships=len(set(additions) & public), entries=tested)
        if tree_type == 'GeometryNodeTree' and bpy.app.version >= (5, 3, 0):
            for query in ('Poisson Solver', '\u6cca\u677e\u6c42\u89e3\u5668', 'bosongqiujieqi', 'bsqjq'):
                assert any(e.node_type == 'GeometryNodeGridSolvePoisson' for e in nc._search_entries(query, set())), query
            node = tree.nodes.new('GeometryNodeCurveToMesh')
            assert node.inputs.get('Miter Scale') is not None
            tree.nodes.remove(node)
            report['checks'].append('Poisson aliases; Curve to Mesh Miter Scale remains a socket')
        if tree_type == 'ShaderNodeTree' and bpy.app.version >= (5, 3, 0):
            for engine, owner in (('CYCLES', 'OBJECT'), ('BLENDER_EEVEE', 'WORLD')):
                context.engine, context.space_data.shader_type = engine, owner
                nc._rebuild_search_entries(context)
                assert not LIGHTS.intersection(e.node_type for e in nc.NODE_SEARCH_ENTRIES if not e.native_hidden)
            context.engine, context.space_data.shader_type = 'BLENDER_EEVEE', 'OBJECT'
            report['checks'].append('EEVEE-only lighting menu visibility; internal light nodes excluded')
        if tree_type == 'CompositorNodeTree' and bpy.app.version >= (5, 3, 0):
            bloom = [e for e in entries if e.kind == 'ASSET' and e.asset_name == 'Bloom']
            assert bloom and all(e.asset_path for e in bloom)
            for entry in bloom:
                node = nc._add_asset_node(context, entry)
                assert node.bl_idname == 'CompositorNodeGroup' and node.node_tree is not None
                tree.nodes.remove(node)
            assert bpy.types.Node.bl_rna_get_subclass('CompositorNodeBloom') is None
            report['checks'].append('bundled Bloom discovered and appended as a real asset group')
        nc._rebuild_search_entries(context)
        snapshot = [(e.identifier, e.menu_paths, e.native_hidden) for e in nc.NODE_SEARCH_ENTRIES]
        nc._clear_search_caches()
        nc._rebuild_search_entries(context)
        assert snapshot == [(e.identifier, e.menu_paths, e.native_hidden) for e in nc.NODE_SEARCH_ENTRIES]
        bpy.data.node_groups.remove(tree)

    with patch.object(nc, '_system_pinyin', return_value=''):
        assert nc._source_pinyin('\u6cca\u677e') == 'bo song'
    report['checks'].append('Poisson scientific pronunciation also works without macOS transliteration')

    # Actual library RNA, including 5.3 is_available(), plus old enabled fallback.
    root = Path(os.environ['BLENDER_USER_CONFIG']) / 'local-assets'
    root.mkdir()
    lib = bpy.context.preferences.filepaths.asset_libraries.new(name='NC test', directory=str(root))
    try:
        assert root in nc._external_asset_node_directories()
        before = nc._asset_index_signature()
        if hasattr(lib, 'enabled'):
            lib.enabled = False
            assert root not in nc._external_asset_node_directories()
            assert nc._asset_index_signature() != before
            assert not nc._asset_library_path_available(root / 'test.blend', nc._asset_library_roots())
            lib.enabled = True
            assert nc._asset_index_signature() == before
        roots = ((str(root), False), (str(root), True))
        assert nc._asset_library_path_available(root / 'same.blend', roots)
        with patch.object(nc, '_asset_library_roots', return_value=((str(root), False),)):
            with patch.object(nc, '_load_asset_index', return_value=[{'path': str(root / 'cached.blend')} ]):
                assert not list(nc._iter_asset_node_groups())
        report['checks'].append('asset-library availability, disabled cache filtering, shared enabled root')
    finally:
        bpy.context.preferences.filepaths.asset_libraries.remove(lib)
    assert all(nc._load_settings()[k] == v for k, v in sentinel.items())
    assert bpy.context.preferences.view.language == ui_language
    report['checks'].append('cold/warm indexes and user settings/language preserved')
    output = Path(sys.argv[sys.argv.index('--') + 1])
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('BLENDER_53_OK', report['version'], report['searches'], report['creations'], report['colors'], report['checks'])


if __name__ == '__main__':
    main()
