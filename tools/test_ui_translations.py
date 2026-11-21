"""UI-copy coverage independent of Blender and the node-search locale."""
import ast
from pathlib import Path
from string import Formatter
import unittest

import addon_updater
import ui_translations as ui

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ast.parse((ROOT / '__init__.py').read_text(encoding='utf-8'))
CHINESE = next(ast.literal_eval(node.value) for node in SOURCE.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == 'UI_TEXT_ZH' for target in node.targets))
CATALOGS = ui.catalogs(CHINESE)


class UITranslationTests(unittest.TestCase):
    def test_all_locales_cover_the_same_messages(self):
        for code in ('zh', 'ja', 'ko', 'ru', 'es'):
            self.assertEqual(set(CATALOGS[code]), set(CATALOGS['zh']), code)
            for key, text in CATALOGS[code].items():
                self.assertIsInstance(text, str)
                self.assertTrue(text.strip(), (code, key))
                fields = lambda value: {name for _, name, _, _ in Formatter().parse(value) if name is not None}
                self.assertEqual(fields(key), fields(text), (code, key))

    def test_manual_ui_calls_and_rna_copy_are_covered(self):
        keys = set()
        for node in ast.walk(SOURCE):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == '_ui_text' and node.args and isinstance(node.args[0], ast.Constant):
                    keys.add(node.args[0].value)
                if node.func.id.endswith('Property'):
                    options = next((kw.value for kw in node.keywords if kw.arg == 'options'), None)
                    if options is not None and 'HIDDEN' in ast.literal_eval(options):
                        continue
                    for kw in node.keywords:
                        if kw.arg in ('name', 'description') and isinstance(kw.value, ast.Constant):
                            keys.add(kw.value.value)
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('bl_label', 'bl_description') for t in node.targets):
                keys.add(ast.literal_eval(node.value))
        keys -= {'', 'Node Console', 'Shift', 'Ctrl', 'Alt', 'Command'}
        self.assertFalse(keys - CATALOGS['zh'].keys(), keys - CATALOGS['zh'].keys())

    def test_no_global_translation_overrides(self):
        for messages in ui.blender_catalog(CATALOGS).values():
            self.assertEqual({key for key in messages if key[0] != ui.CONTEXT},
                             {('*', ui.ADDON_DESCRIPTION)})

    def test_all_release_highlights_are_translated(self):
        for code in ('zh', 'ja', 'ko', 'ru', 'es'):
            self.assertFalse(set(addon_updater.RELEASE_HIGHLIGHTS.values()) - CATALOGS[code].keys())

    def test_interface_locale_resolution(self):
        for language, system, enabled, expected in (
            ('DEFAULT', 'ja_JP', True, 'ja'), ('DEFAULT', 'zh_CN', True, 'zh'),
            ('ko-KR', 'en_US', True, 'ko'), ('ru_RU', 'en_US', True, 'ru'),
            ('es_ES', 'en_US', True, 'es'), ('fr_FR', 'en_US', True, 'en'),
            ('ja_JP', 'en_US', False, 'en')):
            self.assertEqual(ui.language_code(language, system, enabled), expected)

    def test_missing_and_english_text_remain_unchanged(self):
        self.assertEqual(CATALOGS['en'], {})
        self.assertEqual(CATALOGS['ja'].get('User Custom Name', 'User Custom Name'), 'User Custom Name')


if __name__ == '__main__':
    unittest.main()
