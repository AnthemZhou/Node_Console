"""Language normalization/abbreviations, independent of Blender or an IME."""
import unittest
import unicodedata

import search_language as lang
import native_search


class SearchLanguageTests(unittest.TestCase):
    def test_japanese_kana_and_width(self):
        for query in ('ノイズ', 'のいず', 'ﾉｲｽﾞ', unicodedata.normalize('NFD', 'ノイズ')):
            self.assertEqual(lang.search_key(query, 'ja_JP'), 'のいず')
        self.assertEqual(lang.search_key('シェーダー', 'ja_JP'), 'しぇーだー')
        self.assertNotEqual(lang.search_key('ば', 'ja_JP'), lang.search_key('は', 'ja_JP'))
        self.assertEqual(lang.search_key('位置', 'ja_JP'), '位置')

    def test_spanish_accents_but_not_enye(self):
        self.assertEqual(lang.search_key('POSICIO\u0301N', 'es'), 'posicion')
        self.assertEqual(lang.search_key('pingüino', 'es'), 'pinguino')
        self.assertEqual(lang.search_key('AN\u0303O', 'es'), 'año')
        self.assertNotEqual(lang.search_key('año', 'es'), lang.search_key('ano', 'es'))

    def test_russian_e_yo_not_soft_or_hard_signs(self):
        self.assertEqual(lang.search_key('ОБЪЁМ', 'ru_RU'), 'объем')
        self.assertNotEqual(lang.search_key('объём', 'ru_RU'), lang.search_key('обем', 'ru_RU'))
        self.assertNotEqual(lang.search_key('уголь', 'ru_RU'), lang.search_key('угол', 'ru_RU'))

    def test_korean_initials_spacing_and_unfinished_syllable(self):
        profile = lang.profile('노이즈 텍스처', 'ko_KR')
        for query in ('ㄴㅇㅈ', 'ㄴㅇ', 'ᄂᄋᄌ', 'ㅌㅅㅊ', '노ㅇ', '노이즈텍'):
            self.assertGreaterEqual(lang.extension_level(profile, query, 'ko_KR'), 4, query)
        for query in ('ㄴ', 'ㄱㄱ', '노멀', 'noise', ''):
            self.assertEqual(lang.extension_level(profile, query, 'ko_KR'), 0, query)
        self.assertEqual(lang.search_key(unicodedata.normalize('NFD', '노이즈'), 'ko_KR'), '노이즈')
        self.assertEqual(lang.initials('까치'), 'ᄁᄎ')

    def test_profiles_do_not_cross_languages(self):
        self.assertEqual(lang.search_key('ё', 'es'), 'ё')
        self.assertEqual(lang.search_key('á', 'ru_RU'), 'á')
        self.assertEqual(lang.search_key('ノイズ', 'ko_KR'), 'ノイズ')
        for text in ('设置', 'She Zhi', 'ＡＤＤ', '位置', 'año'):
            self.assertEqual(lang.search_key(text, 'zh_HANS'), text)

    def test_folding_preserves_official_sort_keys_and_lengths(self):
        raw = 'Filtrar ▸ Desenfocar ▸ Desenfoque Bokeh'
        original = native_search.Item(raw)
        folded = native_search.Item(lang.search_key(raw, 'es'), source_text=raw)
        self.assertEqual(folded.sort_key, original.sort_key)
        self.assertEqual(folded.main_length, original.main_length)
        self.assertEqual(folded.total_length, original.total_length)
        accented = 'Entrada ▸ Posición'
        folded = native_search.Item(lang.search_key(accented, 'es'), source_text=accented)
        self.assertEqual(folded.main_length, len('Posición'.encode()))
        self.assertEqual(native_search.score(('posicion',), folded), 1010)

    def test_cache_bounded_and_clearable(self):
        for i in range(8300):
            lang.search_key(str(i), 'es')
            lang.query_profile(str(i), 'ko_KR')
        self.assertLessEqual(lang.search_key.cache_info().currsize, 8192)
        self.assertLessEqual(lang.query_profile.cache_info().currsize, 512)
        lang.clear()
        self.assertEqual(lang.search_key.cache_info().currsize, 0)


if __name__ == '__main__':
    unittest.main()
