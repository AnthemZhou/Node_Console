"""Update header layout regressions in a factory-startup Blender process."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import bpy


class Layout:
    def __init__(self, kind='root', parent=None, **props):
        self.kind, self.parent, self.props = kind, parent, props
        self.children = []
        self.enabled = True
        self.alert = False
        self.alignment = 'EXPAND'

    def add(self, kind, **props):
        item = Layout(kind, self, **props)
        self.children.append(item)
        return item

    def row(self, **props):
        return self.add('row', **props)

    def column(self, **props):
        return self.add('column', **props)

    def label(self, **props):
        return self.add('label', **props)

    def separator(self):
        return self.add('separator')

    def operator(self, name, **props):
        return self.add('operator', name=name, **props)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


def main():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('NCPreferencesUITest', root / '__init__.py', submodule_search_locations=[str(root)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    cases = 0
    states = ({'state': 'idle'}, {'state': 'current'}, {'state': 'checking'},
              {'state': 'downloading', 'version': '1.3.1'}, {'state': 'waiting'},
              {'state': 'installed', 'version': '1.3.1', 'backup': '/tmp/previous'},
              {'state': 'updated', 'version': '1.3.1'}, {'state': 'reloading'},
              {'state': 'waiting_reload'}, {'state': 'error', 'code': 'reload_rolled_back'},
              {'state': 'error', 'code': 'offline'})
    for language in ('en_US', 'zh_HANS'):
        bpy.context.preferences.view.language = language
        for width in (1200, 420):
            for state in states:
                layout = Layout()
                context = SimpleNamespace(region=SimpleNamespace(width=width))
                with patch.object(nc, 'UPDATE_STATUS', state), patch.object(nc, '_resolution_scale', return_value=1.0):
                    nc._draw_update_header(layout, context)
                buttons = [item for item in layout.walk() if item.kind == 'operator']
                update = [item for item in buttons if item.props['name'] == 'node_console.update_addon']
                assert len(update) == 1 and update[0].parent.alignment == 'RIGHT'
                assert update[0].props['icon'] == 'FILE_REFRESH'
                if width == 1200 and state['state'] != 'error':
                    assert len(layout.children) == 1, (language, state)
                if state['state'] == 'current':
                    status = next(item for item in layout.walk()
                                  if item.kind == 'label' and item.props['text'] == nc._ui_text('Already up to date'))
                    assert status.parent.enabled is False
                for child in layout.children:
                    if child.kind == 'column':
                        assert child.alert == (state['state'] == 'error')
                        for line in child.children:
                            assert nc._text_width(line.props['text'], 13) <= max(120, width - 160)
                if state.get('backup'):
                    backup = next(item for item in buttons if item.props['name'] == 'wm.path_open')
                    assert backup.filepath == state['backup']
                cases += 1
    print('PREFERENCES_UI_REGRESSION', bpy.app.version_string, cases, 'passed', flush=True)


if __name__ == '__main__':
    main()
