"""Check audit metrics, independent of production search implementation."""
import unittest

from tools.analyze_search_audit import compare, normalize


class AuditMetricsTests(unittest.TestCase):
    def test_short_prefix_is_not_a_complete_match(self):
        result = compare(['a'], ['a', 'b'])
        self.assertTrue(result['exact'])
        self.assertFalse(result['visible_exact'])
        self.assertFalse(result['complete_exact'])
        self.assertEqual(result['extra_results'], ['b'])

    def test_empty_native_is_not_a_vacuous_pass(self):
        result = compare([], ['a'])
        self.assertFalse(result['first'])
        self.assertFalse(result['exact'])
        self.assertFalse(result['visible_exact'])
        self.assertTrue(compare([], [])['visible_exact'])

    def test_native_duplicates_remain_in_strict_metrics(self):
        result = compare(['a', 'a', 'b'], ['a', 'b'])
        self.assertFalse(result['visible_exact'])
        self.assertTrue(result['exact_deduplicated'])
        self.assertEqual(result['native_duplicates'], 1)

    def test_ten_rows_do_not_claim_complete_list_equality(self):
        native = [str(i) for i in range(10)]
        result = compare(native, native + ['hidden'])
        self.assertTrue(result['visible_exact'])
        self.assertFalse(result['native_complete'])
        self.assertIsNone(result['complete_exact'])
        self.assertIsNone(result['extra_results'])

    def test_missing_positions_are_not_dropped(self):
        result = compare(['a', 'b', 'c'], ['a'])
        self.assertEqual(result['position_matches'], 1)
        self.assertEqual(result['missing'], ['b', 'c'])
        self.assertFalse(result['visible_exact'])

    def test_path_normalization_does_not_guess_ocr_typos(self):
        self.assertEqual(normalize('Color > MIX'), normalize('Color \u25b8 Mix'))
        self.assertNotEqual(normalize('\u5408\u5e76XYZ'), normalize('\u5408\u4e95XYZ'))


if __name__ == '__main__':
    unittest.main()
