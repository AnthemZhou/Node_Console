"""Feedback links round-trip user text; no browser or network is used."""
import unittest
from urllib.parse import parse_qs, urlsplit

import issue_report


class IssueReportTests(unittest.TestCase):
    def test_all_supported_languages_and_reserved_characters(self):
        for text in ('中文输入 & # ? + % / @test\n第二行', 'ノイズが見つかりません',
                     '노이즈 검색 문제', 'Ошибка поиска шума', 'Problema con posición y tamaño',
                     'Node search freezes'):
            url = issue_report.draft_url(text, '1.5.0', '5.2.2 LTS', 'darwin', 'zh_HANS')
            parts = urlsplit(url)
            self.assertEqual((parts.scheme, parts.netloc, parts.path),
                             ('https', 'github.com', '/AnthemZhou/Node_Console/issues/new'))
            query = parse_qs(parts.query)
            self.assertEqual(set(query), {'title', 'body'})
            self.assertIn(text, query['body'][0])
            self.assertIn('Node Console: 1.5.0', query['body'][0])
            self.assertNotIn('\n', query['title'][0])

    def test_empty_and_unicode_whitespace(self):
        for text in ('', ' \n\t', '\u3000'):
            with self.assertRaisesRegex(ValueError, 'Describe the problem first'):
                issue_report.draft_url(text, '1.5.0', '5.2', 'win32', 'ja_JP')

    def test_long_reports_rejected_without_truncation(self):
        text = '问题😀' * 2000
        with self.assertRaisesRegex(ValueError, 'too long'):
            issue_report.draft_url(text, '1.5.0', '5.2', 'win32', 'zh_HANS')
        self.assertEqual(text, '问题😀' * 2000)
        valid = issue_report.draft_url('问题' * 250, '1.5.0', '5.2', 'win32', 'zh_HANS')
        self.assertLessEqual(len(valid.encode()), issue_report.MAX_URL_BYTES)
        self.assertIn('问题' * 250, parse_qs(urlsplit(valid).query)['body'][0])

    def test_only_explicit_environment_metadata(self):
        url = issue_report.draft_url('Test', '1.5.0', '5.1.2', 'linux', 'es')
        body = parse_qs(urlsplit(url).query)['body'][0]
        self.assertEqual(body, '### Problem\n\nTest\n\n### Environment\n\n'
            '- Node Console: 1.5.0\n- Blender: 5.1.2\n- Platform: linux\n- Node language: es\n')


if __name__ == '__main__':
    unittest.main()
