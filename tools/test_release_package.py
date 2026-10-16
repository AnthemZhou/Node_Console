"""Check ZIP contents without Blender or local validation reports."""
import contextlib
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from tools import build_local_release


class ReleasePackageTests(unittest.TestCase):
    def check_package(self, include_local_reports):
        sources = (
            '__init__.py', 'addon_updater.py', 'node_registry.py', 'node_search_aliases.json',
            'node_console_builtin_cache.json', 'README.md', 'CHANGELOG.md',
            'PERFORMANCE.md', 'LICENSE',
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in sources:
                shutil.copyfile(build_local_release.ROOT / name, root / name)
            if include_local_reports:
                for report in build_local_release.ROOT.glob('VALIDATION_*.md'):
                    shutil.copyfile(report, root / report.name)
                (root / 'VALIDATION_local.md').write_text('Local report', encoding='utf-8')
                (root / 'Display').mkdir()
                (root / 'Display' / 'private.txt').write_text('Private', encoding='utf-8')

            with patch.object(build_local_release, 'ROOT', root):
                with contextlib.redirect_stdout(io.StringIO()):
                    build_local_release.package_release()

            packages = list(root.glob('Node_Console_*.zip'))
            self.assertEqual(len(packages), 1)
            with ZipFile(packages[0]) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(
                    set(archive.namelist()),
                    {'Node_Console/' + name for name in sources},
                )
                for name in sources:
                    self.assertEqual(archive.read('Node_Console/' + name), (root / name).read_bytes())

    def test_package_without_local_reports(self):
        self.check_package(include_local_reports=False)

    def test_package_excludes_local_reports_and_private_files(self):
        self.check_package(include_local_reports=True)


if __name__ == '__main__':
    unittest.main()
