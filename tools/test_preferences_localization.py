"""Native RNA labels/tooltips, locale switches and user-data preservation."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
view = bpy.context.preferences.view
view.use_translate_interface = True
view.use_translate_tooltips = True
languages = ('en_US', 'zh_HANS', 'ja_JP', 'ko_KR', 'ru_RU', 'es')
global_colors = {}
for language in languages:
    view.language = language
    global_colors[language] = bpy.app.translations.pgettext_iface('Color')

spec = importlib.util.spec_from_file_location('NCPreferencesLocaleTest', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc.register()
addon = bpy.context.preferences.addons.new()
addon.module = nc.ADDON_ID
prefs = addon.preferences
prefs.search_language = 'en_US'
prefs.display_mode = 'ENGLISH'
prefs.scan_asset_libraries = False
data = nc._load_settings()
data.update(favorites=['my-node'], usage={'my-node': 17}, shortcuts=['my-node'], untouched={'user': 'Custom Name'})
nc._write_settings(data)
tree = bpy.data.node_groups.new('UI locale isolation', 'GeometryNodeTree')
context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type='GeometryNodeTree'), engine='BLENDER_EEVEE')
nc._rebuild_search_entries(context)
queries = ('join', 'instance', 'noise', 'add', 'line')
baseline = {query: [e.identifier for e in nc._search_entries(query, set())] for query in queries}
preserved = nc._load_settings()
report = {'version': bpy.app.version_string, 'locales': {}, 'checks': 0}
for language in languages:
    view.language = language
    code = nc._ui_language()
    messages = nc.UI_TEXT[code]
    expected = lambda text: messages.get(text, text)
    assert bpy.app.translations.pgettext_iface('Color') == global_colors[language]
    assert bpy.app.translations.pgettext_iface(nc.bl_info['description']) == expected(nc.bl_info['description'])
    checks = 0
    for prop in prefs.bl_rna.properties:
        if prop.identifier not in nc.ENS_AddonPreferences.__annotations__ or prop.is_hidden:
            continue
        assert prop.translation_context == nc.ui_translations.CONTEXT, prop.identifier
        for text in (prop.name, prop.description):
            assert bpy.app.translations.pgettext_tip(text, prop.translation_context) == expected(text), (language, text)
            checks += 1
        if prop.type == 'ENUM':
            for item in prop.enum_items:
                assert bpy.app.translations.pgettext_iface(item.name, prop.translation_context) == expected(item.name)
                assert bpy.app.translations.pgettext_tip(item.description, prop.translation_context) == expected(item.description)
                checks += 2
    for cls in nc.classes:
        if not issubclass(cls, bpy.types.Operator):
            continue
        assert cls.bl_translation_context == nc.ui_translations.CONTEXT
        for text in (cls.bl_label, cls.bl_description):
            assert bpy.app.translations.pgettext_tip(text, cls.bl_translation_context) == expected(text), (language, cls, text)
            checks += 1
    for key in nc.UI_TEXT['zh']:
        assert nc._ui_text(key) == expected(key)
        checks += 1
    for mode in ('ENGLISH', 'CHINESE', 'ENGLISH_CHINESE', 'CHINESE_ENGLISH'):
        items = nc._display_mode_items(SimpleNamespace(search_language='ja_JP'), None)
        assert items is nc._display_mode_items(SimpleNamespace(search_language='ja_JP'), None)
        source = next(item for item in nc.DISPLAY_MODE_ITEMS['ja_JP'] if item[0] == mode)
        localized = next(item for item in items if item[0] == mode)
        assert localized[:2] == source[:2] and localized[3] == source[3]
        assert localized == source
        assert bpy.app.translations.pgettext_tip(localized[2], nc.ui_translations.CONTEXT) == expected(source[2])
        checks += 1
    release = dict(version='1.6.0', prerelease=False,
                   summary={'zh': 'Blender 5.3 节点支持', 'en': 'Blender 5.3 node support'})
    assert expected('Blender 5.3 node support') in nc._release_label(release)
    assert prefs.search_language == 'en_US' and prefs.display_mode == 'ENGLISH'
    nc._rebuild_search_entries(context)
    assert baseline == {query: [e.identifier for e in nc._search_entries(query, set())] for query in queries}
    assert nc._load_settings() == preserved
    report['locales'][language] = checks
    report['checks'] += checks
view.language = 'ja_JP'
view.use_translate_interface = False
assert nc._ui_text('Update') == 'Update'
text = prefs.bl_rna.properties['ui_scale'].description
assert bpy.app.translations.pgettext_tip(text, nc.ui_translations.CONTEXT) == nc.UI_TEXT['ja'][text]
view.use_translate_tooltips = False
assert bpy.app.translations.pgettext_tip(text, nc.ui_translations.CONTEXT) == text
bpy.data.node_groups.remove(tree)
nc.unregister()
bpy.context.preferences.addons.remove(addon)
view.use_translate_interface = True
view.use_translate_tooltips = True
assert bpy.app.translations.pgettext_iface('Reset Size', nc.ui_translations.CONTEXT) != nc.UI_TEXT['ja']['Reset Size']
output = Path(sys.argv[sys.argv.index('--') + 1])
output.write_text(json.dumps(report, indent=2))
print('PREFERENCES_LOCALE_OK', report, flush=True)
