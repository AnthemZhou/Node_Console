"""Offline updater tests: release selection, ZIP validation, rollback and user data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nc_update_test", ROOT / "addon_updater.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def source(version="1.2.3", blender=(5, 1, 2)):
    return (f"ADDON_VERSION = {version!r}\n"
            f"bl_info = {{'name': 'Node Console', 'version': {updater.version_tuple(version)!r}, 'blender': {blender!r}}}\n")


def release(version="1.2.3", size=1, digest=None):
    filename = f"Node_Console_{version}.zip"
    return {"tag_name": f"v{version}", "draft": False, "prerelease": False,
            "assets": [{"name": filename, "size": size, "state": "uploaded", "digest": digest,
                        "browser_download_url": f"https://github.com/{updater.REPOSITORY}/releases/download/v{version}/{filename}"}]}


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nc-update-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "Node_Console"
        self.target.mkdir()
        (self.target / "__init__.py").write_text(source("1.2.2"))
        (self.target / "node_registry.py").write_text("old = True\n")
        self.archive = self.root / "release.zip"

    def package(self, additions=None, version="1.2.3", blender=(5, 1, 2)):
        contents = {"Node_Console/" + name: "{}" for name in updater.REQUIRED_FILES}
        contents["Node_Console/__init__.py"] = source(version, blender)
        contents["Node_Console/node_registry.py"] = "new = True\n"
        contents.update(additions or {})
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as archive:
            for name, content in contents.items():
                archive.writestr(name, content)
        return self.archive

    def install(self, **kwargs):
        return updater.install_release(self.archive, self.target, "1.2.3", (5, 2, 2), **kwargs)

    def assert_error(self, code, operation):
        with self.assertRaises(updater.UpdateError) as raised:
            operation()
        self.assertEqual(raised.exception.code, code)
        self.assertEqual((self.target / "__init__.py").read_text(), source("1.2.2"))

    def test_version_comparison_and_stable_releases(self):
        self.assertIsNone(updater.select_release(release("1.2.2"), "1.2.2"))
        self.assertIsNone(updater.select_release(release("1.2.1"), "1.2.2"))
        self.assertEqual(updater.select_release(release("1.10.0"), "1.9.9")["version"], "1.10.0")
        for tag in ("v1.2.3-beta", "main", None, "1.2", "1.2.03"):
            with self.subTest(tag=tag), self.assertRaises(updater.UpdateError):
                updater.version_tuple(tag)
        for key in ("draft", "prerelease"):
            data = release()
            data[key] = True
            self.assert_error("invalid_release", lambda: updater.select_release(data, "1.2.2"))

    def test_only_exact_repository_install_asset(self):
        for key, value in (("name", "Source-code.zip"), ("size", 0), ("size", updater.MAX_DOWNLOAD + 1),
                           ("browser_download_url", "https://github.com/someone/else/file.zip"),
                           ("digest", "sha256:wrong")):
            data = release()
            data["assets"][0][key] = value
            with self.subTest(key=key), self.assertRaises(updater.UpdateError):
                updater.select_release(data, "1.2.2")
        data = release()
        data["assets"] *= 2
        self.assert_error("missing_package", lambda: updater.select_release(data, "1.2.2"))

    def test_download_host_and_redirect_restrictions(self):
        for url in ("http://github.com/file", "https://github.com.evil.test/file", "https://user:pass@github.com/file",
                    "file:///tmp/file", "https://github.com:9999/file"):
            with self.subTest(url=url), self.assertRaises(updater.UpdateError):
                updater._safe_url(url)
        updater._safe_url("https://release-assets.githubusercontent.com/github-production-release-asset/file")
        with self.assertRaises(updater.UpdateError):
            updater._GithubRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test/file")

    def test_backup_and_user_data_are_preserved(self):
        self.package()
        personal = {"node_console_settings.json": '{"favorites":["Math"],"usage":{"Math":7}}',
                    "my_snippets.json": '{"snippets":["custom"]}', "notes.txt": "keep"}
        for name, value in personal.items():
            (self.target / name).write_text(value)
        outside = self.root / "outside-library.json"
        outside.write_text("library")
        other_addon = self.root / "AnotherAddon"
        other_addon.mkdir()
        (other_addon / "__init__.py").write_text("unchanged")
        (self.target / "__pycache__").mkdir()
        (self.target / "__pycache__" / "old.pyc").write_bytes(b"stale")
        backup = self.install(protected_paths=(outside, self.target / "my_snippets.json"), current_version="1.2.2")
        self.assertEqual((self.target / "__init__.py").read_text(), source())
        self.assertEqual((backup / "__init__.py").read_text(), source("1.2.2"))
        self.assertTrue(backup.parent.name.startswith(".node-console-update-"))
        self.assertFalse((self.target / "__pycache__").exists())
        for name, value in personal.items():
            self.assertEqual((self.target / name).read_text(), value)
            self.assertEqual((backup / name).read_text(), value)
        self.assertEqual(outside.read_text(), "library")
        self.assertEqual((other_addon / "__init__.py").read_text(), "unchanged")

    def test_user_data_collision_is_blocked(self):
        self.package({"Node_Console/my_snippets.json": "{}"})
        personal = self.target / "my_snippets.json"
        personal.write_text("personal")
        self.assert_error("protected_data", lambda: self.install(protected_paths=(personal,)))
        self.assertEqual(personal.read_text(), "personal")
        self.package({"Node_Console/node_console_settings.json": "{}"})
        self.assert_error("invalid_package", self.install)

    def test_zip_traversal_and_unexpected_content(self):
        for name in ("../escape.py", "/absolute.py", "Node_Console/../escape.py", "Node_Console\\escape.py",
                     "Node_Console/C:/file.py", "Node_Console/.git/config", "Node_Console/__pycache__/x.pyc",
                     "Node_Console/payload.exe", "__init__.py", "Node_Console/CON.txt",
                     "Node_Console/directory./file.py", "Node_Console/directory /file.py"):
            with self.subTest(name=name):
                self.package({name: ""})
                self.assert_error("invalid_package", self.install)
        self.assertFalse((self.root / "escape.py").exists())

    def test_symlinks_and_case_collisions_in_zip(self):
        self.package()
        link = ZipInfo("Node_Console/link.py")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with ZipFile(self.archive, "a") as archive:
            archive.writestr(link, "../outside.py")
        self.assert_error("invalid_package", self.install)
        self.package({"Node_Console/NODE_REGISTRY.py": "x = 1"})
        self.assert_error("invalid_package", self.install)

    def test_existing_symlink_is_not_followed(self):
        self.package()
        outside = self.root / "private.py"
        outside.write_text("personal")
        (self.target / "node_registry.py").unlink()
        (self.target / "node_registry.py").symlink_to(outside)
        self.assert_error("unsafe_install", self.install)
        self.assertEqual(outside.read_text(), "personal")

    def test_incompatible_or_mislabelled_packages(self):
        self.package(version="1.2.4")
        self.assert_error("invalid_package", self.install)
        self.package(blender=(5, 3, 0))
        self.assert_error("incompatible_blender", self.install)
        self.archive.write_bytes(b"not a zip")
        self.assert_error("invalid_package", self.install)
        self.package({"Node_Console/node_registry.py": "def broken("})
        self.assert_error("invalid_package", self.install)

    def test_development_checkout_and_changed_install_blocked(self):
        self.package()
        (self.target / ".git").write_text("gitdir: somewhere")
        self.assert_error("development_install", self.install)
        (self.target / ".git").unlink()
        self.assert_error("changed_install", lambda: self.install(current_version="1.2.1"))
        self.assert_error("changed_install", lambda: updater.install_release(self.archive, self.target, "1.2.1", (5, 2, 2)))

    def test_second_rename_failure_rolls_back(self):
        self.package()
        rename = Path.rename

        def fail_staged(path, destination):
            if path.name == "new":
                raise OSError("simulated replace failure")
            return rename(path, destination)

        with patch.object(Path, "rename", fail_staged), self.assertRaises(OSError):
            self.install()
        self.assertEqual((self.target / "__init__.py").read_text(), source("1.2.2"))
        self.assertEqual(list(self.root.glob(".node-console-update-*")), [])

    def test_copy_failure_keeps_original_files(self):
        self.package()
        with patch.object(updater.shutil, "copytree", side_effect=PermissionError), self.assertRaises(PermissionError):
            self.install()
        self.assertEqual((self.target / "__init__.py").read_text(), source("1.2.2"))

    def run_download(self, data=None, error=None, corrupt=False):
        self.package()
        blob = self.archive.read_bytes()
        data = data or release(size=len(blob), digest="sha256:" + hashlib.sha256(blob).hexdigest())
        jobdir = self.root / "download"
        jobdir.mkdir(exist_ok=True)

        def fetch(_url, destination=None, **_kwargs):
            if error:
                raise error
            if destination:
                destination.write_bytes(b"x" * len(blob) if corrupt else blob)
            else:
                return json.dumps(data).encode()

        with patch.object(updater, "_fetch", side_effect=fetch):
            updater.download_release(jobdir, "1.2.2")
        return json.loads((jobdir / "result.json").read_text())

    def test_download_and_digest(self):
        self.assertEqual(self.run_download()["state"], "ready")
        self.assertEqual(self.run_download(corrupt=True)["code"], "invalid_package")
        self.assertEqual(self.run_download(data=release("1.2.2"))["state"], "current")

    def test_network_errors_and_rate_limits(self):
        for error, code in ((URLError("offline"), "network_error"), (TimeoutError(), "network_error"),
                            (HTTPError(updater.LATEST_URL, 403, "rate", {}, None), "rate_limit"),
                            (HTTPError(updater.LATEST_URL, 404, "missing", {}, None), "no_release")):
            with self.subTest(code=code):
                self.assertEqual(self.run_download(error=error)["code"], code)

    def test_job_cancel_and_timeout(self):
        process = Mock()
        process.poll.return_value = None
        with patch.object(updater.subprocess, "Popen", return_value=process) as popen:
            job = updater.UpdateJob("1.2.2")
        self.assertEqual(popen.call_args.args[0][1], "-I")
        self.assertEqual(job.poll()["state"], "checking")
        job.started -= updater.JOB_TIMEOUT + 1
        self.assertEqual(job.poll()["code"], "network_error")
        process.poll.return_value = 0
        process.returncode = 0
        updater._write_result(job.directory, {"state": "ready", "version": "1.2.3"})
        self.assertEqual(job.poll()["state"], "ready")
        process.poll.return_value = None
        job.close()
        process.terminate.assert_called_once()
        self.assertFalse(job.directory.exists())

    def test_worker_start_failure_removes_temporary_files(self):
        directory = self.root / "job"
        directory.mkdir()
        with patch.object(updater.tempfile, "mkdtemp", return_value=str(directory)), \
                patch.object(updater.subprocess, "Popen", side_effect=OSError), self.assertRaises(OSError):
            updater.UpdateJob("1.2.2")
        self.assertFalse(directory.exists())

    def test_download_and_unpacked_size_limits(self):
        response = Mock()
        response.geturl.return_value = updater.LATEST_URL
        response.headers = {"Content-Length": "999"}
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch.object(updater, "build_opener") as opener:
            opener.return_value.open.return_value = response
            self.assert_error("invalid_release", lambda: updater._fetch(updater.LATEST_URL, limit=10))
            response.headers = {}
            response.read.side_effect = [b"12345678901", b""]
            self.assert_error("invalid_release", lambda: updater._fetch(updater.LATEST_URL, limit=10))
        self.package()
        with patch.object(updater, "MAX_UNPACKED", 1):
            self.assert_error("invalid_package", self.install)


if __name__ == "__main__":
    unittest.main()
