"""Real RNA enum registration and editor-specific snippet category regressions."""
import importlib.util
import inspect
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import bpy


def main():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('NCCategoryTest', root / '__init__.py',
                                                submodule_search_locations=[str(root)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)

    annotations = inspect.get_annotations(nc.NODECONSOLE_OT_SaveSnippet, eval_str=True)

    class CategoryProbe(bpy.types.PropertyGroup):
        category: annotations['category']
        category_tree_id: annotations['category_tree_id']
        snippet_name: bpy.props.StringProperty()

    bpy.utils.register_class(nc.NODECONSOLE_OT_SaveSnippet)
    bpy.utils.register_class(CategoryProbe)
    bpy.types.WindowManager.nc_category_probe = bpy.props.PointerProperty(type=CategoryProbe)
    trees = []
    try:
        assert 'category' in bpy.ops.node_console.save_snippet.get_rna_type().properties
        props = bpy.context.window_manager.nc_category_probe
        assert props.category == 'NONE'
        assert [item[0] for item in nc._snippet_category_enum_items(None, None)] == ['NONE']
        numeric_values = {}
        for tree_id in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree') * 2:
            tree = bpy.data.node_groups.new('Category test', tree_id)
            trees.append(tree)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree),
                window_manager=SimpleNamespace(invoke_props_dialog=Mock(return_value={'RUNNING_MODAL'})))
            node = tree.nodes.new('NodeReroute')
            node.select = True
            assert nc.NODECONSOLE_OT_SaveSnippet.invoke(props, context, None) == {'RUNNING_MODAL'}
            assert props.category_tree_id == tree_id and props.category == 'NONE'
            items = nc._snippet_category_enum_items(props, None)
            ids = {item[0] for item in items}
            assert ('FILTER' in ids) == (tree_id == 'CompositorNodeTree')
            assert ('MASK' in ids) == (tree_id == 'CompositorNodeTree')
            assert ('DISTORT' in ids) == (tree_id == 'CompositorNodeTree')
            assert ('SHADER' in ids) == (tree_id == 'ShaderNodeTree')
            assert ('GEOMETRY' in ids) == (tree_id == 'GeometryNodeTree')
            assert {'COLOR', 'VECTOR', 'TEXTURE', 'UTILITY', 'NONE'} <= ids
            for item in items:
                props.category = item[0]
                assert props.category == item[0]
                assert numeric_values.setdefault(item[0], item[3]) == item[3]
            wrong_context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=SimpleNamespace(bl_idname='WrongTree')))
            assert nc._snippet_category_enum_items(props, wrong_context) is items
            terminal = tree.nodes.new('CompositorNodeBlur' if tree_id == 'CompositorNodeTree' else 'ShaderNodeMath')
            terminal.select = True
            tree.links.new(node.outputs[0], terminal.inputs[0])
            expected = 'FILTER' if tree_id == 'CompositorNodeTree' else 'CONVERTER'
            assert nc.NODECONSOLE_OT_SaveSnippet.invoke(props, context, None) == {'RUNNING_MODAL'}
            assert props.category == expected
            tree.links.clear()
            assert nc.NODECONSOLE_OT_SaveSnippet.invoke(props, context, None) == {'RUNNING_MODAL'}
            assert props.category == 'NONE'
            nc.NODECONSOLE_OT_SaveSnippet.cancel(props, context)
            assert nc.ACTIVE_SNIPPET_DIALOG is None
        assert nc._coerce_snippet_category_for_tree('FILTER', 'GeometryNodeTree') == 'NONE'
        assert nc._coerce_snippet_category_for_tree('CUSTOM', 'ShaderNodeTree') == 'NONE'
        print('SNIPPET_CATEGORY_REGRESSION', bpy.app.version_string, 'passed', flush=True)
    finally:
        for tree in trees:
            bpy.data.node_groups.remove(tree)
        del bpy.types.WindowManager.nc_category_probe
        bpy.utils.unregister_class(CategoryProbe)
        bpy.utils.unregister_class(nc.NODECONSOLE_OT_SaveSnippet)


if __name__ == '__main__':
    main()
