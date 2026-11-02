"""Read official Python node menus without changing Blender's UI language.

Only built-in bl_ui functions are evaluated. Translation functions are rebound
in private function namespaces, never patched in Blender's shared modules.
C++ asset menus continue to use Node Console's existing asset discovery.
"""
import ast
import inspect
from types import FunctionType, MethodType, SimpleNamespace

import bpy

ARROW = '\u25b8'


def context_signature(context):
    space = context.space_data
    tree = getattr(space, 'edit_tree', None)
    owner = getattr(space, 'id_from', None)
    return (getattr(context, 'engine', getattr(bpy.context, 'engine', '')),
            getattr(space, 'shader_type', 'OBJECT'),
            getattr(space, 'node_tree_sub_type', '') or (
                'TOOL' if getattr(tree, 'is_tool', False) else
                'SEQUENCER' if getattr(tree, 'is_strip_modifier', False) else
                'SCENE' if getattr(tree, 'bl_idname', '') == 'CompositorNodeTree' else 'MODIFIER'),
            getattr(owner, 'type', 'MESH'))


def semantic_key(node_type, settings):
    # Socket numerical defaults don't identify variants; enum sockets do.
    values = [(name, repr(value)) for name, value in settings
              if not name.startswith('inputs[') or isinstance(value, str)]
    return node_type, tuple(sorted(values))


class Settings(list):
    def add(self):
        item = SimpleNamespace(name='', value='')
        self.append(item)
        return item


class MenuContext:
    is_menu_search = True

    def __init__(self, context):
        self.original = context
        source = context.space_data
        engine, shader_type, sub_type, owner_type = context_signature(context)
        self.engine = engine
        self.space_data = SimpleNamespace(
            type='NODE_EDITOR', tree_type=source.tree_type,
            edit_tree=source.edit_tree, node_tree=source.edit_tree,
            shader_type=shader_type, node_tree_sub_type=sub_type,
            geometry_nodes_type=getattr(source, 'geometry_nodes_type', 'MODIFIER'),
            id_from=getattr(source, 'id_from', SimpleNamespace(type=owner_type)))

    def __getattr__(self, name):
        return getattr(self.original, name, getattr(bpy.context, name, None))


class Collector:
    def __init__(self, context, translate):
        self.context = MenuContext(context)
        self.translate = translate
        self.functions = {}
        self.rows = []
        self.errors = []
        self.active = set()

    def function(self, function):
        if function not in self.functions:
            namespace = dict(function.__globals__)
            for name in ('iface_', 'n_', 'tip_'):
                if name in namespace:
                    namespace[name] = self.translate
            self.functions[function] = FunctionType(function.__code__, namespace,
                function.__name__, function.__defaults__, function.__closure__)
            self.functions[function].__kwdefaults__ = function.__kwdefaults__
        return self.functions[function]

    def draw(self, name, path):
        cls = getattr(bpy.types, name, None) or bpy.types.Menu.bl_rna_get_subclass_py(name)
        if cls is None or not hasattr(cls, 'draw') or name in self.active:
            return
        function = cls.draw
        # Do not execute arbitrary add-on menus in a synthetic layout/context.
        if not getattr(function, '__module__', '').startswith('bl_ui.'):
            return
        if hasattr(cls, 'poll') and not cls.poll(self.context):
            return
        collector = self
        class Proxy:
            layout = Layout(collector, path)

            def __getattr__(self, attr):
                value = getattr(cls, attr)
                if inspect.ismethod(value) and value.__func__.__module__.startswith('bl_ui.'):
                    return MethodType(collector.function(value.__func__), self)
                return value
        self.active.add(name)
        try:
            self.function(function)(Proxy(), self.context)
        except (AttributeError, TypeError, ValueError, RuntimeError) as error:
            self.errors.append((name, str(error)))
        finally:
            self.active.remove(name)


class Layout:
    operator_context = 'INVOKE_REGION_WIN'

    def __init__(self, collector, path):
        self.collector, self.path = collector, path

    def operator(self, operator, text='', text_ctxt='*', translate=True,
                 search_weight=0.0, **_kwargs):
        props = SimpleNamespace(settings=Settings(), use_transform=True)
        if translate:
            text = self.collector.translate(text, text_ctxt)
        path = self.path or [self.collector.translate('Add', 'Operator')]
        self.collector.rows.append((operator, ' '+ARROW+' ', path+[text], search_weight, props))
        return props

    def menu(self, name, text=None, **_kwargs):
        cls = getattr(bpy.types, name, None) or bpy.types.Menu.bl_rna_get_subclass_py(name)
        if cls:
            label = text if text is not None else cls.bl_label
            label = self.collector.translate(label, getattr(cls, 'bl_translation_context', '*'))
            self.collector.draw(name, self.path+[label])

    def menu_contents(self, name, **_kwargs):
        self.collector.draw(name, self.path)

    def template_node_asset_menu_items(self, **_kwargs):
        pass

    def separator(self, *_args, **_kwargs):
        pass

    separator_spacer = separator
    label = separator


def collect(context, chinese_translate):
    """Return semantic identities mapped to bilingual paths and menu weights."""
    languages = []
    errors = []
    for translate in (lambda text, context='*': text, chinese_translate):
        collector = Collector(context, translate)
        collector.draw('NODE_MT_add', [])
        languages.append(collector.rows)
        errors.extend(collector.errors)
    paths = {}
    if len(languages[0]) != len(languages[1]):
        return {}, [('NODE_MT_add', 'Translation changed menu structure')]
    for english, chinese in zip(*languages):
        operator, separator, parts, weight, props = english
        if operator not in {'node.add_node', 'node.add_zone'}:
            continue
        settings = []
        for setting in props.settings:
            try:
                settings.append((setting.name, ast.literal_eval(setting.value)))
            except (ValueError, TypeError, SyntaxError):
                # Expressions referencing local data-blocks are handled live.
                settings.append((setting.name, setting.value))
        if hasattr(props, 'visible_output'):
            settings.append(('visible_output', props.visible_output))
        if operator == 'node.add_zone':
            key = ('ZONE', props.input_node_type, props.output_node_type)
        else:
            key = semantic_key(getattr(props, 'type', ''), settings)
        row = (separator.join(parts), separator.join(chinese[2]), float(weight))
        paths.setdefault(key, []).append(row)
    return {key: tuple(dict.fromkeys(rows)) for key, rows in paths.items()}, errors
