"""Complete-syllable reverse lookup without Blender or an IME dictionary."""
import unittest

from pinyin_search import QueryIndex

READINGS = {
    '\u5b9e\u4f8b': 'shi li', '\u5b9e\u4f8b\u5316\u4e8e\u70b9\u4e0a': 'shi li hua yu dian shang',
    '\u968f\u673a\u53d8\u6362': 'sui ji bian huan', '\u5b9e\u73b0\u5b9e\u4f8b': 'shi xian shi li',
    '\u77e2\u91cf': 'shi liang', '\u989c\u8272': 'yan se', '\u6df7\u5408': 'hun he',
    '\u4ea4\u70b9': 'jiao dian', '\u7126\u70b9': 'jiao dian',
    '\u5b9e\u4f8b \u8f6c\u4e3a \u70b9': 'shi li zhuan wei dian',
}


def profiles(text):
    parts = READINGS[text].split()
    boundaries, offset = [], 0
    for part in parts:
        offset += len(part)
        boundaries.append(offset)
    return [(''.join(parts), tuple(boundaries), '', '')]


class PinyinSearchTests(unittest.TestCase):
    def test_category_leaf_and_infix_share_original_text(self):
        index = QueryIndex(['\u5b9e\u4f8b \u25b8 \u968f\u673a\u53d8\u6362',
                            '\u5b9e\u4f8b\u5316\u4e8e\u70b9\u4e0a', '\u5b9e\u73b0\u5b9e\u4f8b'], profiles)
        self.assertEqual(index.resolve('shili'), ('\u5b9e\u4f8b',))
        self.assertEqual(index.resolve('SHI LI'), ('\u5b9e\u4f8b',))
        self.assertEqual(index.resolve('  shi  li  '), ('\u5b9e\u4f8b',))
        self.assertEqual(index.resolve('bianhuan'), ('\u53d8\u6362',))

    def test_no_partial_syllables_or_initials_decoded_as_chinese(self):
        index = QueryIndex(['\u77e2\u91cf'], profiles)
        for query in ('shili', 'hiliang', 'sliang', 'sl', 'shil', ''):
            self.assertEqual(index.resolve(query), (), query)
        self.assertEqual(index.resolve('shiliang'), ('\u77e2\u91cf',))

    def test_homophones_preserve_both_spellings(self):
        index = QueryIndex(['\u4ea4\u70b9', '\u7126\u70b9'], profiles)
        self.assertEqual(index.resolve('jiaodian'), ('\u4ea4\u70b9', '\u7126\u70b9'))

    def test_spaced_label_and_cross_category_words(self):
        index = QueryIndex(['\u5b9e\u4f8b \u8f6c\u4e3a \u70b9', '\u989c\u8272 \u25b8 \u6df7\u5408'], profiles)
        self.assertEqual(index.resolve('shilizhuanweidian'), ('\u5b9e\u4f8b \u8f6c\u4e3a \u70b9',))
        self.assertEqual(index.resolve('yanse hunhe'), ('\u989c\u8272 \u6df7\u5408',))

    def test_unknown_and_non_latin_queries_do_not_translate(self):
        index = QueryIndex(READINGS, profiles)
        for query in ('zzzz', 'noise', '\u5b9e\u4f8b', 'shi2li', 'shili*'):
            self.assertEqual(index.resolve(query), ())

    def test_malformed_reading_does_not_guess_character_offsets(self):
        index = QueryIndex(['\u5b9e\u4f8b'], lambda text: [('shili', (5,), '', '')])
        self.assertEqual(index.resolve('shili'), ())

    def test_alternate_reading_keeps_original_chinese_spelling(self):
        index = QueryIndex(['\u6805\u683c'], lambda text: [
            ('zhage', (3, 5), '', ''), ('shange', (4, 6), '', '')])
        self.assertEqual(index.resolve('zhage'), ('\u6805\u683c',))
        self.assertEqual(index.resolve('shange'), ('\u6805\u683c',))

    def test_excessive_ambiguity_falls_back_instead_of_expanding_forever(self):
        index = QueryIndex([chr(0x4e00 + i) for i in range(17)],
                           lambda text: [('shi', (3,), '', '')])
        self.assertEqual(index.resolve('shi'), ())
        self.assertEqual(index.resolve('shi shi'), ())


if __name__ == '__main__':
    unittest.main()
