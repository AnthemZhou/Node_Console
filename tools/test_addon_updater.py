"""Offline updater tests: release selection, ZIP validation, rollback and user data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
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

    def test_prerelease_version_order_and_labels(self):
        ordered = ["1.4.0", "1.4.1-alpha.1", "1.4.1-beta.1", "1.4.1-beta.2",
                   "1.4.1-beta.10", "1.4.1-rc.1", "1.4.1", "1.4.2"]
        self.assertEqual(sorted(reversed(ordered), key=updater.version_key), ordered)
        self.assertEqual(updater.version_tuple("v1.4.1-beta.1"), (1, 4, 1))
        for invalid in ("1.4.1-beta.0", "1.4.1-beta.01", "1.4.1-nightly.1", "1.4.1/other"):
            with self.assertRaises(updater.UpdateError):
                updater.version_key(invalid)

    def test_check_lists_stable_and_opt_in_beta_without_downloading(self):
        beta = dict(release("1.4.2-beta.1"), prerelease=True)
        bad_beta = release("1.4.3-beta.1")
        data = [release("1.4.0"), beta, release("1.4.1"), bad_beta,
                dict(release("9.0.0"), draft=True), {"tag_name": "invalid"}]
        with patch.object(updater, "_fetch", return_value=json.dumps(data).encode()) as fetch:
            self.assertEqual([item["version"] for item in updater.list_releases()], ["1.4.1", "1.4.0"])
            self.assertEqual([item["version"] for item in updater.list_releases(True)],
                             ["1.4.2-beta.1", "1.4.1", "1.4.0"])
            self.assertTrue(all("destination" not in call.kwargs for call in fetch.call_args_list))

    def test_release_pagination_and_bounded_list(self):
        pages = [json.dumps([release(f"1.1.{i}") for i in range(100)]).encode(),
                 json.dumps([release("1.4.0")]).encode()]
        with patch.object(updater, "_fetch", side_effect=pages) as fetch:
            found = updater.list_releases()
            self.assertEqual(found[0]["version"], "1.4.0")
            self.assertEqual([item["version"] for item in found], ["1.4.0", "1.1.99", "1.1.98"])
            self.assertIn("page=2", fetch.call_args_list[1].args[0])

    def test_three_choices_after_channel_filter_and_version_sort(self):
        data = [release("1.4.0"), dict(release("1.4.2-beta.1"), prerelease=True),
                release("1.4.1"), release("1.3.4"), release("1.3.3"),
                dict(release("1.4.2-rc.1"), prerelease=True)]
        with patch.object(updater, "_fetch", return_value=json.dumps(data).encode()):
            self.assertEqual([item["version"] for item in updater.list_releases()],
                             ["1.4.1", "1.4.0", "1.3.4"])
            self.assertEqual([item["version"] for item in updater.list_releases(True)],
                             ["1.4.2-rc.1", "1.4.2-beta.1", "1.4.1"])

    def test_all_online_update_versions_have_short_highlights(self):
        versions = re.findall(r"^## (\d+\.\d+\.\d+(?:-[a-z]+\.\d+)?)", (ROOT / "CHANGELOG.md").read_text(), re.MULTILINE)
        expected = {version for version in versions if updater.version_key(version) >= updater.version_key("1.3.0")}
        self.assertEqual(set(updater.RELEASE_HIGHLIGHTS), expected)
        for highlight in updater.RELEASE_HIGHLIGHTS.values():
            self.assertTrue(highlight.isprintable() and 0 < len(highlight) <= 72)

    def test_future_release_summary_comes_from_explicit_metadata(self):
        summary = {"en": "Faster startup", "zh": "\u542f\u52a8\u63d0\u901f"}
        data = dict(release("1.5.0-beta.1"), prerelease=True,
                    body="Notes\n<!-- node-console-summary: " + json.dumps(summary) + " -->\nMore notes")
        with patch.object(updater, "_fetch", return_value=json.dumps([data]).encode()) as fetch:
            records = updater.list_releases(True)
        self.assertEqual(records[0]["summary"], summary)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(records[0]["version"], "1.5.0-beta.1")

    def test_bad_summary_never_hides_an_installable_release(self):
        for body in (None, [], "Ordinary release notes", '<!-- node-console-summary: nope -->',
                     '<!-- node-console-summary: [] -->',
                     '<!-- node-console-summary: {"en": 42} -->',
                     '<!-- node-console-summary: {"en": ""} -->',
                     '<!-- node-console-summary: {"en": "line\\nbreak"} -->',
                     '<!-- node-console-summary: {"en": "hidden\\u202e"} -->',
                     '<!-- node-console-summary: ' + json.dumps({"en": "x" * 73, "zh": "x" * 33}) + ' -->'):
            with self.subTest(body=body):
                record = updater.release_record(dict(release("1.5.0"), body=body))
                self.assertNotIn("summary", record)
                self.assertEqual(record["version"], "1.5.0")

    def test_summary_languages_validate_independently(self):
        self.assertEqual(updater._release_summary(
            '<!-- node-console-summary: {"en": "  Faster startup  ", "zh": 42, "extra": "ignored"} -->'),
            {"en": "Faster startup"})
        self.assertEqual(updater._release_summary(
            'Notes\r\n<!-- node-console-summary: {"en": "Faster startup"} -->\r\nMore notes'),
            {"en": "Faster startup"})

    def test_current_changelog_metadata_matches_offline_highlight(self):
        changelog = (ROOT / "CHANGELOG.md").read_text()
        version = re.search(r"^## (\S+)", changelog, re.MULTILINE)[1]
        self.assertEqual(updater._release_summary(changelog)["en"], updater.RELEASE_HIGHLIGHTS[version])

    def test_check_worker_never_downloads_or_changes_installed_files(self):
        jobdir = self.root / "check"
        jobdir.mkdir()
        (jobdir / "request.json").write_text(json.dumps({"action": "check", "allow_beta": False}))
        with patch.object(updater, "_fetch", return_value=json.dumps([release()]).encode()) as fetch:
            updater.run_job(jobdir)
        result = json.loads((jobdir / "result.json").read_text())
        self.assertEqual(result["state"], "releases")
        self.assertFalse((jobdir / "release.zip").exists())
        self.assertEqual((self.target / "__init__.py").read_text(), source("1.2.2"))
        self.assertEqual(fetch.call_count, 1)

    def selected_download(self, changed=False, beta=False, opt_in=True, corrupt=False, summary=False):
        self.package()
        blob = self.archive.read_bytes()
        data = release(size=len(blob), digest="sha256:" + hashlib.sha256(blob).hexdigest())
        data["prerelease"] = beta
        if summary:
            data["body"] = '<!-- node-console-summary: {"en": "Faster startup"} -->'
        selected = updater.release_record(data, allow_beta=True)
        jobdir = self.root / "selected"
        jobdir.mkdir(exist_ok=True)
        (jobdir / "request.json").write_text(json.dumps({"action": "install", "release": selected, "allow_beta": opt_in}))
        if changed:
            data["assets"][0]["digest"] = "sha256:" + "0" * 64

        def fetch(url, destination=None, **kwargs):
            if destination:
                destination.write_bytes(b"x" * len(blob) if corrupt else blob)
            else:
                self.assertEqual(url, updater.RELEASES_URL + "/tags/v1.2.3")
                return json.dumps(data).encode()

        with patch.object(updater, "_fetch", side_effect=fetch) as fetched:
            updater.run_job(jobdir)
        return json.loads((jobdir / "result.json").read_text()), fetched

    def test_selected_tag_is_pinned_and_revalidated(self):
        result, fetched = self.selected_download()
        self.assertEqual(result, {"state": "ready", "version": "1.2.3", "tag": "v1.2.3"})
        self.assertEqual(fetched.call_count, 2)
        result, fetched = self.selected_download(changed=True)
        self.assertEqual(result["code"], "changed_release")
        self.assertEqual(fetched.call_count, 1)
        self.assertEqual(self.selected_download(corrupt=True)[0]["code"], "invalid_package")

    def test_beta_cannot_download_without_explicit_opt_in(self):
        self.assertEqual(self.selected_download(beta=True, opt_in=False)[0]["code"], "invalid_release")
        self.assertEqual(self.selected_download(beta=True, opt_in=True)[0]["state"], "ready")

    def test_summary_keeps_download_verification_intact(self):
        self.assertEqual(self.selected_download(summary=True)[0]["state"], "ready")
        self.assertEqual(self.selected_download(summary=True, changed=True)[0]["code"], "changed_release")

    def test_downgrade_requires_explicit_flag_and_unchanged_current_version(self):
        self.package(version="1.2.1")
        for kwargs in ({}, {"allow_downgrade": True},
                       {"allow_downgrade": True, "current_version": "1.2.0"}):
            self.assert_error("changed_install", lambda: updater.install_release(
                self.archive, self.target, "1.2.1", (5, 2, 2), **kwargs))
        personal = self.target / "node_console_settings.json"
        personal.write_text('{"favorites":["keep"]}')
        backup = updater.install_release(self.archive, self.target, "1.2.1", (5, 2, 2),
                                         current_version="1.2.2", allow_downgrade=True)
        self.assertIn("1.2.1", (self.target / "__init__.py").read_text())
        self.assertEqual(personal.read_text(), '{"favorites":["keep"]}')
        self.assertIn("1.2.2", (backup / "__init__.py").read_text())

    def test_beta_package_version_must_match_exactly(self):
        self.package(version="1.2.3")
        self.assert_error("invalid_package", lambda: updater.install_release(
            self.archive, self.target, "1.2.3-beta.1", (5, 2, 2)))
        self.package(version="1.2.3-beta.1")
        updater.install_release(self.archive, self.target, "1.2.3-beta.1", (5, 2, 2))
        self.assertIn("1.2.3-beta.1", (self.target / "__init__.py").read_text())

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
