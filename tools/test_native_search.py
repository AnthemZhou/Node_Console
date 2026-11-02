"""Pure Python matching tests, including upstream Blender test vectors."""
import unittest
import native_search as search


class NativeSearchTests(unittest.TestCase):
    def test_upstream_cases(self):
        self.assertEqual(search.self_test()['upstream_fixtures'], 19)

    def test_unicode_and_ascii_normalization(self):
        self.assertEqual(search.words('Noise-Texture/foo_bar'),
                         (('noise', 'texture', 'foo', 'bar'), (0, 0, 0, 0)))
        self.assertEqual(search.distance('集合', '集和'), 1)
        self.assertEqual(search.distance('实例', '例实'), 1)

    def test_prefix_initials_and_typo(self):
        item = search.Item('Add \u25b8 Texture \u25b8 Noise Texture')
        self.assertEqual(search.score(('noise',), item), 1010)
        self.assertEqual(search.score(('nt',), item), 1004)
        self.assertIsNotNone(search.score(('niose',), item))
        self.assertIsNone(search.score(('zzzzzzz',), item))

    def test_query_words_cannot_reuse_item_words(self):
        item = search.Item('T \u25b8 Test')
        self.assertIsNotNone(search.score(('t', 'test'), item))
        self.assertIsNone(search.score(('test', 'test'), item))

    def test_name_match_beats_category(self):
        category = search.Item('Noise \u25b8 Test', 100)
        leaf = search.Item('Other \u25b8 Noise', 0)
        self.assertEqual(search.search([category, leaf], 'noise'), [leaf, category])

    def test_weight_only_changes_highest_score_bucket(self):
        items = [search.Item('Add \u25b8 Mesh Line'),
                 search.Item('Add \u25b8 Curve Line', 2),
                 search.Item('Line \u25b8 Curve', 100)]
        self.assertEqual(search.search(items, 'line'), [items[1], items[0], items[2]])

    def test_recent_only_for_empty_or_one_byte_queries(self):
        old = search.Item('Add \u25b8 Mesh', recent=0)
        recent = search.Item('Add \u25b8 Mesh Line', recent=1)
        self.assertEqual(search.search([old, recent], '')[0], recent)
        self.assertEqual(search.search([old, recent], 'm')[0], recent)
        self.assertEqual(search.search([old, recent], 'me')[0], old)
        cn = [search.Item('集合', recent=0), search.Item('集合信息', recent=1)]
        self.assertEqual(search.search(cn, '集')[0], cn[0])

    def test_deprecated_and_word_order(self):
        item = search.Item('Add \u25b8 Set Position')
        self.assertGreater(search.score(('set', 'position'), item),
                           search.score(('position', 'set'), item))
        deprecated = search.Item('Deprecated \u25b8 Set Position')
        self.assertEqual(search.score(('set',), item) - search.score(('set',), deprecated), 500)

    def test_bounded_caches_and_clear(self):
        for i in range(8500):
            search.fuzzy(str(i), 'test')
            search.words(str(i))
        self.assertLessEqual(search.fuzzy.cache_info().currsize, 8192)
        self.assertLessEqual(search.words.cache_info().currsize, 4096)
        search.clear()
        self.assertEqual(search.words.cache_info().currsize, 0)
        self.assertEqual(search.fuzzy.cache_info().currsize, 0)


if __name__ == '__main__':
    unittest.main()
