"""Shortcut rows and drag events in an isolated Blender process."""
import contextlib
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


def event(kind, value='PRESS', x=100, y=87, **kwargs):
    return SimpleNamespace(type=kind, value=value, mouse_region_x=x, mouse_region_y=y,
                           unicode='', ctrl=False, alt=False, oskey=False, **kwargs)


def main():
    spec = importlib.util.spec_from_file_location(
        'NCShortcutTest', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    passed = []
    # Run the real modal methods without a UI window or registering user keymaps.
    Console = type('ConsoleHarness', (), {
        key: value for key, value in nc.ENS_AddNodeByEnglishSearch.__dict__.items()
        if not key.startswith('__')})
    entries = [nc.NodeSearchEntry(name, 'Geometry', name, name, name, '', 'NODE')
               for name in ('a', 'b', 'c')]
    context = SimpleNamespace(area=SimpleNamespace(tag_redraw=Mock()))

    def console():
        op = Console()
        op._tree_id = GEOMETRY
        op._shortcuts = ['a', 'b', 'c']
        op._favorites = {'b'}
        op._panel_rect = (0, 0, 400, 140)
        op._rows_top = 100
        op._padding = 8
        op._row_height = 26
        op._visible_limit = 3
        op._owns_context = lambda ctx: True
        op._confirm = Mock(return_value={'FINISHED'})
        op._reset_shortcut_drag()
        op._refresh_results()
        nc.ACTIVE_CONSOLE_OPERATOR = op
        return op

    def ids(op):
        return [entry.identifier for entry in op._results]

    with tempfile.TemporaryDirectory(prefix='nc-shortcut-test-') as directory:
        nc._settings_path = lambda: Path(directory) / 'settings.json'
        nc._preferences = lambda: None
        nc._ui_scale = lambda: 1.0
        nc.NODE_ENTRY_BY_ID = {entry.identifier: entry for entry in entries}
        nc.NODE_SEARCH_ENTRIES = entries
        initial = {
            'shortcuts': ['a', 'missing', 'b', 'c'],
            'shortcut_tree_meta': {'a': [GEOMETRY, SHADER], 'b': [GEOMETRY, SHADER],
                                   'missing': [GEOMETRY], 'c': [GEOMETRY]},
            'favorites': ['b'], 'usage': {'b': 7}, 'console_width': 405,
            'unrelated_setting': {'keep': True},
        }
        nc._write_settings(initial)
        assert nc._load_shortcuts_for_tree(GEOMETRY) == ['a', 'missing', 'b', 'c']
        nc._save_shortcut_order_for_tree(GEOMETRY, ['b', 'c', 'a', 'a', 'unknown'])
        assert nc._load_shortcuts_for_tree(GEOMETRY) == ['b', 'missing', 'c', 'a']
        assert nc._load_shortcuts_for_tree(SHADER) == ['a', 'b']
        for key, value in initial.items():
            assert nc._load_settings()[key] == value, key
        nc._move_shortcut('a', -1, GEOMETRY)
        assert nc._load_shortcuts_for_tree(GEOMETRY) == ['b', 'missing', 'a', 'c']
        assert nc._load_shortcuts_for_tree(SHADER) == ['a', 'b']
        passed.append('tree-specific order preserves missing nodes and unrelated settings')

        nc._write_settings(initial)
        op = console()
        assert ids(op) == ['a', 'b', 'c']
        op.modal(context, event('LEFTMOUSE'))
        assert not op._confirm.called
        result = op.modal(context, event('LEFTMOUSE', 'RELEASE'))
        assert result == {'FINISHED'} and op._confirm.call_count == 1
        assert nc._load_settings() == initial
        passed.append('click creates only on release without writing settings')

        op = console()
        op.modal(context, event('LEFTMOUSE'))
        op.modal(context, event('MOUSEMOVE', 'NOTHING', y=35))
        assert ids(op) == ['b', 'c', 'a'] and not op._confirm.called
        assert nc._load_settings() == initial
        op.modal(context, event('LEFTMOUSE', 'RELEASE', y=35))
        assert nc._load_shortcuts_for_tree(GEOMETRY) == ['b', 'missing', 'c', 'a']
        assert not op._confirm.called and op._shortcut_press_identifier is None
        passed.append('drag previews locally and commits only on release')

        for cancel in (event('ESC'), event('RIGHTMOUSE'), event('WINDOW_DEACTIVATE'),
                       event('LEFTMOUSE', 'RELEASE', x=500, y=35)):
            nc._write_settings(initial)
            op = console()
            op.modal(context, event('LEFTMOUSE'))
            op.modal(context, event('MOUSEMOVE', 'NOTHING', y=35))
            op.modal(context, cancel)
            assert ids(op) == ['a', 'b', 'c'] and not op._confirm.called
            assert nc._load_settings() == initial
        passed.append('escape, right-click, focus loss and outside release cancel drag')

        op = console()
        op.modal(context, event('LEFTMOUSE'))
        op.modal(context, event('MOUSEMOVE', 'NOTHING', y=85))
        op.modal(context, event('LEFTMOUSE', 'RELEASE', y=85))
        assert op._confirm.call_count == 1
        assert nc._load_settings() == initial
        passed.append('small pointer movement is still a click')

        op = console()
        op.modal(context, event('DOWN_ARROW'))
        assert op._selected_index == 0 and op._keyboard_selection_active
        op.modal(context, event('DOWN_ARROW'))
        assert op._selected_index == 1
        op.modal(context, event('RET'))
        assert op._confirm.called
        op = console()
        with patch.object(nc, '_search_entries', return_value=[entries[1]]) as search:
            op._query = 'b'
            op._refresh_results()
            assert ids(op) == ['b'] and search.call_count == 1
        op._snippet_mode = True
        with patch.object(nc, '_search_snippets', return_value=[]) as search:
            op._query = ''
            op._refresh_results()
            assert not op._results and search.call_count == 1
        passed.append('keyboard selection, queries and snippets retain separate behavior')

        op = console()
        op._context_menu_kind = 'SHORTCUT'
        op._context_menu_shortcut = 'b'
        op._context_menu_action_from_mouse = lambda evt: 'REMOVE_SHORTCUT'
        op.modal(context, event('LEFTMOUSE'))
        assert ids(op) == ['a', 'c']
        assert nc._load_shortcuts_for_tree(SHADER) == ['a', 'b']
        passed.append('right-click removal refreshes rows without changing other editors')

        nc._write_settings(initial)
        nc._save_shortcut_order_for_tree(GEOMETRY, ['c', 'a', 'b'])
        nc._remove_shortcut('c', GEOMETRY)
        nc._add_shortcut('c', GEOMETRY)
        assert nc._load_shortcuts_for_tree(GEOMETRY) == ['missing', 'a', 'b', 'c']
        passed.append('removed and re-added shortcuts append rather than reuse stale order')

        for invalid in (None, [], {'GeometryNodeTree': None}, {'GeometryNodeTree': ['a', {}, 'a', 'missing-id']}):
            nc._write_settings(dict(initial, shortcut_order_by_tree=invalid))
            assert nc._load_shortcuts_for_tree(GEOMETRY) == ['a', 'missing', 'b', 'c']
        passed.append('malformed or obsolete order metadata falls back to saved shortcuts')

        nc._write_settings(initial)
        op = console()
        op._visible_limit = 2
        op._panel_rect = (0, 40, 400, 100)
        op.modal(context, event('LEFTMOUSE'))
        op.modal(context, event('MOUSEMOVE', 'NOTHING', y=50))
        op.modal(context, event('TIMER'))
        assert op._scroll_offset == 1 and ids(op) == ['b', 'c', 'a']
        op.modal(context, event('LEFTMOUSE', 'RELEASE', y=50))
        assert nc._load_shortcuts_for_tree(GEOMETRY) == ['b', 'missing', 'c', 'a']
        passed.append('edge timer scrolls during drag without creating nodes')

        # Exercise actual row layout and display helpers, but avoid GPU drawing in background.
        op = console()
        draw_context = SimpleNamespace(region=SimpleNamespace(width=900, height=600))
        op._anchor_x, op._anchor_y = 450, 400
        draw_names = ('_draw_rounded_panel', '_draw_rounded_rect', '_draw_rect', '_draw_text',
                      '_draw_centered_text', '_draw_horizontal_fade', '_draw_right_rounded_fill',
                      '_draw_label_text')
        for mode in ('LINE', 'BLOCK', 'NONE'):
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(nc, '_category_color_mode', return_value=mode))
                mocks = {name: stack.enter_context(patch.object(nc, name)) for name in draw_names}
                op._draw_callback(draw_context)
                labels = mocks['_draw_label_text'].call_args_list
                assert len(labels) == 3
                assert labels[0].args[2] > labels[1].args[2] > labels[2].args[2]
                assert op._panel_rect[1] >= 0
        passed.append('shortcut rows use normal category and label rendering in all color modes')

        for query, snippet in (('', False), ('node', False), ('snippet', True)):
            for mode in ('LINE', 'BLOCK', 'NONE'):
                op = console()
                op._query, op._snippet_mode = query, snippet
                op._results = [nc.replace(entry, kind='SNIPPET') for entry in entries] if snippet else entries
                op._anchor_x, op._anchor_y = 450, 400
                with contextlib.ExitStack() as stack:
                    stack.enter_context(patch.object(nc, '_category_color_mode', return_value=mode))
                    mocks = {name: stack.enter_context(patch.object(nc, name)) for name in draw_names}

                    def highlighted_rows():
                        panel = mocks['_draw_rounded_panel']
                        panel.reset_mock()
                        op._draw_callback(draw_context)
                        return [call for call in panel.call_args_list if call.args[5] == nc.HIGHLIGHT_COLOR]

                    assert not highlighted_rows(), (query, snippet, mode)
                    op.modal(context, event('TIMER'))
                    assert not highlighted_rows()
                    row_x = op._panel_rect[0] + op._padding + 20
                    row_y = op._rows_top - op._row_height * 1.5
                    op.modal(context, event('MOUSEMOVE', 'NOTHING', x=row_x, y=row_y))
                    assert op._hovered_result_index == 1 and len(highlighted_rows()) == 1
                    op.modal(context, event('MOUSEMOVE', 'NOTHING', x=0, y=0))
                    assert op._hovered_result_index is None and not highlighted_rows()
                    op.modal(context, event('DOWN_ARROW'))
                    assert op._selected_index == 0 and len(highlighted_rows()) == 1
                    op.modal(context, event('DOWN_ARROW'))
                    assert op._selected_index == 1 and len(highlighted_rows()) == 1
                    op.modal(context, event('RET'))
                    op._confirm.assert_called_once()
        passed.append('initial/timer rows are unhighlighted; hover, leave and arrow keys work in every mode')

        op = console()
        op.modal(context, event('RET'))
        assert op._selected_index == 0 and op._confirm.call_count == 1
        op = console()
        op._context_menu_kind, op._context_menu_shortcut = 'SHORTCUT', 'b'
        op._anchor_x, op._anchor_y = 450, 400
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(nc, '_category_color_mode', return_value='BLOCK'))
            stack.enter_context(patch.object(nc, '_draw_text_vcenter'))
            mocks = {name: stack.enter_context(patch.object(nc, name)) for name in draw_names}
            op._draw_callback(draw_context)
            assert len([call for call in mocks['_draw_rounded_panel'].call_args_list
                        if call.args[5] == nc.HIGHLIGHT_COLOR]) == 1
        passed.append('implicit Enter and right-click target emphasis are retained')

        many = [nc.NodeSearchEntry(str(i), 'Geometry', str(i), str(i), str(i), '', 'NODE')
                for i in range(18)]
        nc.NODE_ENTRY_BY_ID = {entry.identifier: entry for entry in many}
        op = console()
        op._shortcuts = list(nc.NODE_ENTRY_BY_ID)
        op._refresh_results()
        assert len(op._results) == 18
        op._visible_limit = 12
        assert op._scroll_results(6)
        assert op._results[op._scroll_offset + op._visible_limit - 1].identifier == '17'
        passed.append('more than ten shortcuts remain accessible by scrolling')

        for _ in range(2):
            nc.register()
            try:
                properties = bpy.ops.node_console.move_shortcut.get_rna_type().properties
                assert 'tree_id' in properties, list(properties.keys())
            finally:
                nc.unregister()
        passed.append('new properties survive native register, unregister and re-register')

    report = {'version': bpy.app.version_string, 'passed': passed}
    if '--' in sys.argv:
        Path(sys.argv[sys.argv.index('--') + 1]).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('SHORTCUT_UI_REGRESSION', bpy.app.version_string, len(passed), 'passed', flush=True)


if __name__ == '__main__':
    main()
