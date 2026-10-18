"""Data freshness, creation and failed-save behavior in a factory Blender process."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location('NCUserDataTest', ROOT / '__init__.py',
                                                submodule_search_locations=[str(ROOT)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    passed = []
    with tempfile.TemporaryDirectory(prefix='nc-user-data-') as directory:
        root = Path(directory)
        nc._settings_path = lambda: root / 'settings.json'
        nc._snippets_path = lambda: root / 'snippets.json'
        nc._preferences = lambda: None
        settings = {'favorites': ['snippet:one'], 'usage': {'kept': 42},
                    'future_field': {'nested': [1, 2]},
                    'search_index_cache': {'old': [{'label': 'kept'}]}}
        nc._write_settings(settings)
        assert nc._load_favorites() == {'snippet:one'}
        nc._settings_path().write_text(json.dumps(dict(settings, favorites=['external'])), encoding='utf-8')
        assert nc._load_favorites() == {'external'}
        nc._save_shortcuts(['new'])
        assert all(nc._load_settings()[key] == value for key, value in settings.items() if key != 'favorites')
        passed.append('external settings refresh; unrelated values survive writes')

        tree = bpy.data.node_groups.new('User data test', 'GeometryNodeTree')
        context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree,
                                  tree_type=tree.bl_idname, cursor_location=Vector((100, 200))),
                                  area=SimpleNamespace(tag_redraw=Mock()))
        try:
            frame = tree.nodes.new('NodeFrame')
            frame.label = 'Original'
            first = tree.nodes.new('ShaderNodeMath')
            second = tree.nodes.new('ShaderNodeMath')
            first.parent = second.parent = frame
            tree.links.new(first.outputs[0], second.inputs[0])
            snippet = dict(id='one', name='Saved', tree_type=tree.bl_idname, category='CONVERTER',
                           payload=nc._serialize_snippet_nodes(tree, set(tree.nodes), frame))
            nc._save_snippets([snippet])
            entry = nc._search_snippets('', tree.bl_idname, set())[0]
            summary = nc._snippet_search_snapshot()['snippets'][0]
            assert 'payload' not in summary
            assert (summary['node_count'], summary['link_count']) == (3, 1)
            assert nc._snippet_summaries([{'payload': {'nodes': None, 'links': False}}]) == [
                {'node_count': 0, 'link_count': 0}]
            passed.append('search metadata excludes graph payload and tolerates invalid counts')
            snippet['payload']['nodes'][0]['label'] = 'Externally edited'
            nc._snippets_path().write_text(json.dumps({'snippets': [snippet]}), encoding='utf-8')
            inserted = nc._insert_snippet(context, entry)
            assert inserted.label == 'Externally edited'
            assert len(tree.nodes) == 6 and len(tree.links) == 2
            passed.append('insert rechecks external edits and recreates nodes and links')
            nc._snippets_path().write_text('{"snippets": []}', encoding='utf-8')
            assert nc._insert_snippet(context, entry) is None and len(tree.nodes) == 6
            passed.append('deleted snippet cannot be created from a stale result')

            reports = Mock()
            op = SimpleNamespace(snippet_name='Not saved', category='CONVERTER',
                                 cancel=lambda context: None, report=reports)

            def state():
                return [(node.as_pointer(), node.parent.as_pointer() if node.parent else None,
                         tuple(node.location), node.label, node.select) for node in tree.nodes]

            # Both existing and automatically created frames must roll back on failure.
            for with_frame in (True, False):
                for node in tree.nodes:
                    node.select = node in ({frame, first, second} if with_frame else {first, second})
                before = state()
                contents = nc._snippets_path().read_bytes()
                with patch.object(nc.SNIPPETS_STORE, 'write', side_effect=OSError('disk full')):
                    assert nc.NODECONSOLE_OT_SaveSnippet.execute(op, context) == {'CANCELLED'}
                assert state() == before
                assert nc._snippets_path().read_bytes() == contents
                assert reports.call_args.args[0] == {'ERROR'}
            passed.append('failed save reports error and restores existing/new frames')

            nc._save_snippets([snippet])
            nc._write_settings(settings)
            console = SimpleNamespace(_results=[entry], _tree_id=tree.bl_idname, report=reports)
            with patch.object(nc.SNIPPETS_STORE, 'write', side_effect=PermissionError('read only')):
                nc.ENS_AddNodeByEnglishSearch._remove_snippet_result(console, 0)
                remove_op = SimpleNamespace(snippet_id='one', report=reports)
                assert nc.NODECONSOLE_OT_RemoveSnippet.execute(remove_op, context) == {'CANCELLED'}
            assert nc._load_snippets() == [snippet]
            assert nc._load_favorites() == {'snippet:one'}
            passed.append('failed deletion keeps the snippet and its favorite')

            alternate = root / 'alternate.json'
            alternate.write_text('{"snippets": []}', encoding='utf-8')
            with patch.object(nc, '_snippets_path', return_value=alternate):
                assert not nc._search_snippets('', tree.bl_idname, set())
            assert nc._search_snippets('', tree.bl_idname, set())[0].identifier == 'snippet:one'
            passed.append('switching libraries invalidates entries without mixing identities')
        finally:
            bpy.data.node_groups.remove(tree)
    print('USER_DATA_REGRESSION', bpy.app.version_string, len(passed), 'passed', flush=True)


if __name__ == '__main__':
    main()
