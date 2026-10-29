"""Native resource integrity, caching and non-macOS fallback; no UI or real prefs."""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import ime_input
from ime_input import library


class ResourceTests(unittest.TestCase):
    def test_bundled_resource_matches_source_and_version(self):
        resource = json.loads(library.RESOURCE.read_text())
        source = library.RESOURCE.with_name("ime_cocoa.m")
        self.assertEqual(resource["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(set(resource["architectures"]), {"arm64", "x86_64"})
        with tempfile.TemporaryDirectory() as directory:
            result = library.materialize(cache=directory)
            self.assertEqual(hashlib.sha256(result.read_bytes()).hexdigest(), resource["sha256"])
            before = result.stat().st_mtime_ns
            self.assertEqual(library.materialize(cache=directory), result)
            self.assertEqual(result.stat().st_mtime_ns, before)
            result.write_bytes(b"corrupt cached file")
            self.assertEqual(library.materialize(cache=directory).read_bytes(), base64.b64decode(resource["data"]))

    def test_invalid_resource_is_not_materialized(self):
        good = json.loads(library.RESOURCE.read_text())
        for changes in ({"sha256": "0" * 64}, {"version": "../../bad"}, {"format": 2}, {"data": "!"}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                resource = root / "resource.json"
                resource.write_text(json.dumps(dict(good, **changes)))
                with self.assertRaises(ValueError):
                    library.materialize(resource, root / "cache")
                self.assertFalse((root / "cache").exists())

    def test_other_platforms_do_not_patch_console_or_load_resource(self):
        module = SimpleNamespace(ENS_AddNodeByEnglishSearch=Mock())
        for platform in ("win32", "linux"):
            with patch.object(ime_input.sys, "platform", platform), patch.object(library, "materialize") as load:
                self.assertIsNone(ime_input.install_if_available(module))
                load.assert_not_called()
                module.ENS_AddNodeByEnglishSearch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
