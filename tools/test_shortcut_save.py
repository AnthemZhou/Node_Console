"""Atomic shortcut additions through the real modal handler; no user data touched."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bpy

ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = 'GeometryNodeTree'
SHADER = 'ShaderNodeTree'


def load(name, root, settings):
    spec = importlib.util.spec_from_file_location(name, root / '__init__.py', submodule_search_locations=[str(root)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[name] = nc
    spec.loader.exec_module(nc)
    nc._settings_path = lambda: settings
    nc._preferences = lambda: None
    return nc


def console(nc, identifier='test:shortcut'):
    entry = nc.NodeSearchEntry(identifier, 'Geometry', 'Noise', '\u566a\u6ce2', 'Noise', '', 'NODE')
    nc.NODE_ENTRY_BY_ID = {entry.identifier: entry}
    Harness = type('ConsoleHarness', (), {k: v for k, v in nc.ENS_AddNodeByEnglishSearch.__dict__.items()
                                         if not k.startswith('__')})
    op = Harness()
    op._owns_context = lambda ctx: True
    op._tree_id = GEOMETRY
    op._query = 'noise'
    op._favorite_meta = {}
    op._favorites = set()
    op._shortcuts = []
    op._results = [entry]
    op._context_menu_kind = 'NODE'
    op._context_menu_index = 0
    op._context_menu_action_from_mouse = lambda event: 'SHORTCUT'
    op.report = Mock()
    nc.ACTIVE_CONSOLE_OPERATOR = op
    context = SimpleNamespace(area=SimpleNamespace(tag_redraw=Mock()))
    event = SimpleNamespace(type='LEFTMOUSE', value='PRESS', unicode='', ctrl=False, alt=False, oskey=False)
    return op, context, event


def main():
    with tempfile.TemporaryDirectory(prefix='nc-shortcut-save-') as directory:
        path = Path(directory) / 'settings.json'
        nc = load('NCShortcutSaveTest', ROOT, path)
        initial = {'favorites': ['kept'], 'favorite_tree_meta': {'kept': [SHADER]},
                   'usage': {'kept': 42}, 'future': {'kept': [1, 2]},
                   'shortcut_order_by_tree': {SHADER: ['kept']},
                   'search_index_cache': {'large': [{'label': 'untouched'}] * 2000}}
        nc._write_settings(initial)
        op, context, event = console(nc)
        with patch.object(nc.json_store.os, 'replace', wraps=nc.json_store.os.replace) as replace, \
                patch.object(nc, '_load_settings', side_effect=AssertionError('Full settings copy')):
            assert op.modal(context, event) == {'RUNNING_MODAL'}
        assert replace.call_count == 1
        assert not op.report.called and op._query == ''
        assert op._shortcuts == ['test:shortcut'] and op._results[0].identifier == 'test:shortcut'
        saved = nc._load_settings()
        assert all(saved[key] == value for key, value in initial.items())
        assert saved['shortcut_tree_meta'] == {'test:shortcut': [GEOMETRY]}
        assert saved['favorite_meta'] == {'test:shortcut': 'Noise'}
        with patch.object(nc.json_store.os, 'replace', wraps=nc.json_store.os.replace) as replace:
            assert nc._add_shortcut('test:shortcut', GEOMETRY, 'Noise')
        replace.assert_not_called()
        assert nc._add_shortcut('test:shortcut', SHADER, 'Noise')
        assert nc._load_shortcuts_for_tree(SHADER) == ['test:shortcut']
        assert nc._load_shortcuts_for_tree(GEOMETRY) == ['test:shortcut']
        assert len(nc._load_shortcuts()) == 1
        for failure in ('replace', 'fsync'):
            before = path.read_bytes()
            op, context, event = console(nc, 'failed:shortcut')
            with patch.object(nc.json_store.os, failure, side_effect=OSError('test disk failure')):
                assert op.modal(context, event) == {'RUNNING_MODAL'}
            assert op.report.call_args.args[0] == {'ERROR'}
            assert op._query == 'noise' and not op._shortcuts
            assert path.read_bytes() == before
        path.write_text('{broken', encoding='utf-8')
        assert not nc._add_shortcut('failed:shortcut', GEOMETRY, 'Noise')
        assert path.read_text() == '{broken'
        print('SHORTCUT_SAVE_REGRESSION', bpy.app.version_string, 'passed', flush=True)


if __name__ == '__main__':
    main()
