"""Run with Blender --background --factory-startup --python, then -- output.json."""
import gettext
import json
import sys
from pathlib import Path

import bpy


def audit():
    catalog_path = Path(bpy.utils.resource_path('LOCAL')) / 'datafiles/locale/zh_HANS/LC_MESSAGES/blender.mo'
    with catalog_path.open('rb') as source:
        catalog = gettext.GNUTranslations(source)
    result = {'version': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode(),
              'catalog': str(catalog_path), 'trees': {}, 'experimental': {}}
    exp = bpy.context.preferences.experimental
    for prop in exp.bl_rna.properties:
        if prop.type == 'BOOLEAN':
            result['experimental'][prop.identifier] = getattr(exp, prop.identifier)
    classes = []
    for name in dir(bpy.types):
        cls = getattr(bpy.types, name)
        if isinstance(cls, type) and issubclass(cls, bpy.types.Node):
            if cls.bl_rna.identifier == name and bpy.types.Node.bl_rna_get_subclass(name):
                classes.append((name, cls))
    for tree_type in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
        tree = bpy.data.node_groups.new('Node Console audit', tree_type)
        records = {}
        for name, cls in classes:
            try:
                python_poll = bool(cls.poll(tree))
            except (TypeError, RuntimeError, AttributeError):
                python_poll = None
            try:
                node = tree.nodes.new(name)
            except Exception:
                continue
            rna = cls.bl_rna
            label = node.bl_label or rna.name
            context = rna.translation_context
            translated = catalog.pgettext(context, label) if context and context != '*' else catalog.gettext(label)
            if translated == label:
                translated = catalog.gettext(label)
            records[name] = {'label': label, 'rna_name': rna.name, 'context': context,
                             'chinese': translated, 'color_tag': node.color_tag,
                             'bl_idname': node.bl_idname, 'python_poll': python_poll}
            tree.nodes.remove(node)
        result['trees'][tree_type] = records
        bpy.data.node_groups.remove(tree)
    return result


if __name__ == '__main__':
    output = Path(sys.argv[sys.argv.index('--') + 1])
    data = audit()
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('AUDIT', data['version'], {key: len(value) for key, value in data['trees'].items()})
