"""Runtime node capabilities and language-independent Blender translations."""
import gettext
import json
from pathlib import Path

import bpy

INDEX_SCHEMA = 2
_catalog = None
_inventories = {}
_aliases = None


def clear():
    global _catalog
    _catalog = None
    _inventories.clear()


def runtime_signature(tree):
    experimental = bpy.context.preferences.experimental
    switches = tuple((p.identifier, getattr(experimental, p.identifier))
                     for p in experimental.bl_rna.properties if p.type == 'BOOLEAN')
    flags = tuple((name, getattr(tree, name, False))
                  for name in ('is_tool', 'is_modifier', 'is_strip_modifier'))
    return (tuple(bpy.app.version), bpy.app.build_hash.decode(), tree.bl_idname, flags, switches)


def node_classes():
    # Built-in RNA classes need not define Python bl_idname/bl_label attributes.
    for name in dir(bpy.types):
        cls = getattr(bpy.types, name)
        if isinstance(cls, type) and issubclass(cls, bpy.types.Node):
            if cls.bl_rna.identifier == name and bpy.types.Node.bl_rna_get_subclass(name):
                yield cls


def inventory(tree):
    key = runtime_signature(tree)
    if key in _inventories:
        return _inventories[key]
    supported = {}
    probe = bpy.data.node_groups.new('.Node Console capability probe', tree.bl_idname)
    try:
        for name, value in key[3]:
            if hasattr(probe, name):
                try:
                    setattr(probe, name, value)
                except (AttributeError, TypeError):
                    pass
        for cls in node_classes():
            node_type = cls.bl_rna.identifier
            try:
                if 'poll' in cls.__dict__ and not cls.poll(tree):
                    continue
            except (AttributeError, TypeError, RuntimeError):
                # Inherited Python poll is narrower than native cross-editor
                # support. nodes.new invokes the authoritative native poll.
                pass
            try:
                node = probe.nodes.new(node_type)
            except (RuntimeError, TypeError):
                continue
            supported[node_type] = {
                'english': cls.bl_rna.name,
                'context': cls.bl_rna.translation_context,
                'color_tag': getattr(node, 'color_tag', 'NONE'),
            }
            probe.nodes.remove(node)
    finally:
        bpy.data.node_groups.remove(probe)
    _inventories[key] = supported
    return supported


def catalog():
    global _catalog
    if _catalog is None:
        _catalog = gettext.NullTranslations()
        for kind in ('LOCAL', 'SYSTEM'):
            root = bpy.utils.resource_path(kind)
            if not root:
                continue
            for language in ('zh_HANS', 'zh_CN'):
                path = Path(root) / 'datafiles/locale' / language / 'LC_MESSAGES/blender.mo'
                if path.is_file():
                    try:
                        with path.open('rb') as source:
                            _catalog = gettext.GNUTranslations(source)
                        return _catalog
                    except (OSError, ValueError, EOFError):
                        continue
    return _catalog


def aliases():
    global _aliases
    if _aliases is None:
        path = Path(__file__).with_name('node_search_aliases.json')
        _aliases = json.loads(path.read_text(encoding='utf-8'))['aliases'] if path.exists() else {}
    return _aliases


def chinese_label(text, context=None):
    translation = catalog()
    if context and context != '*':
        result = translation.pgettext(context, text)
        if result != text:
            return result
    result = translation.gettext(text)
    if result != text:
        return result
    # These are explicitly editorial search aliases, not official translations.
    return next((alias for alias in aliases().get(text, ())
                 if any('\u4e00' <= char <= '\u9fff' for char in alias)), text)
