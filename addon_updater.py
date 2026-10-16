"""User-initiated GitHub updates. No Blender API calls or background threads."""
from __future__ import annotations

import ast
import atexit
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile


REPOSITORY = "AnthemZhou/Node_Console"
LATEST_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
MAX_DOWNLOAD = 32 * 1024 * 1024
MAX_UNPACKED = 128 * 1024 * 1024
TIMEOUT = 20
JOB_TIMEOUT = 180
PROTECTED_NAMES = {"node_console_settings.json", "node_console_snippets.json"}
REQUIRED_FILES = {"__init__.py", "node_registry.py", "node_search_aliases.json",
                  "node_console_builtin_cache.json"}
WINDOWS_DEVICE_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}


class UpdateError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(detail or code)
        self.code = code


def version_tuple(value):
    match = re.fullmatch(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", str(value))
    if not match:
        raise UpdateError("invalid_release")
    return tuple(int(part) for part in match.groups())


def _safe_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or parsed.port not in (None, 443)
            or parsed.hostname not in {"api.github.com", "github.com",
                                       "release-assets.githubusercontent.com",
                                       "objects.githubusercontent.com"}):
        raise UpdateError("invalid_release", "Unexpected download host")


class _GithubRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _safe_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(url, destination=None, limit=MAX_DOWNLOAD):
    _safe_url(url)
    request = Request(url, headers={"User-Agent": "Node-Console-Updater",
                                   "Accept": "application/octet-stream" if destination else "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28"})
    context = ssl.create_default_context()
    # Blender's bundled Python may have no OpenSSL default CA path (notably macOS).
    try:
        import certifi
    except ImportError:
        pass
    else:
        context.load_verify_locations(cafile=certifi.where())
    data = bytearray()
    with build_opener(_GithubRedirect(), HTTPSHandler(context=context)).open(request, timeout=TIMEOUT) as response:
        _safe_url(response.geturl())
        if int(response.headers.get("Content-Length", 0)) > limit:
            raise UpdateError("invalid_release", "Download is too large")
        stream = destination.open("wb") if destination else None
        try:
            count = 0
            while chunk := response.read(64 * 1024):
                count += len(chunk)
                if count > limit:
                    raise UpdateError("invalid_release", "Download is too large")
                if stream:
                    stream.write(chunk)
                else:
                    data.extend(chunk)
        finally:
            if stream:
                stream.close()
    return bytes(data)


def select_release(data, current_version):
    if not isinstance(data, dict) or data.get("draft") is not False or data.get("prerelease") is not False:
        raise UpdateError("invalid_release")
    version = version_tuple(data.get("tag_name"))
    if version <= version_tuple(current_version):
        return None
    label = ".".join(map(str, version))
    filename = f"Node_Console_{label}.zip"
    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise UpdateError("invalid_release")
    matching = [item for item in assets if isinstance(item, dict) and item.get("name") == filename]
    if len(matching) != 1:
        raise UpdateError("missing_package")
    asset = matching[0]
    expected_url = f"https://github.com/{REPOSITORY}/releases/download/{data['tag_name']}/{filename}"
    if (asset.get("browser_download_url") != expected_url or asset.get("state") != "uploaded"
            or type(asset.get("size")) is not int or not 0 < asset["size"] <= MAX_DOWNLOAD):
        raise UpdateError("invalid_release")
    digest = asset.get("digest") or ""
    if digest and not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
        raise UpdateError("invalid_release")
    return {"version": label, "url": expected_url, "size": asset["size"], "digest": digest.lower()}


def _write_result(directory, result):
    pending = directory / "result.tmp"
    pending.write_text(json.dumps(result), encoding="utf-8")
    pending.replace(directory / "result.json")


def download_release(directory, current_version):
    """Only the child Python process performs network I/O."""
    try:
        release = select_release(json.loads(_fetch(LATEST_URL, limit=2 * 1024 * 1024)), current_version)
        if release is None:
            _write_result(directory, {"state": "current"})
            return
        _write_result(directory, {"state": "downloading", "version": release["version"]})
        archive = directory / "release.zip"
        _fetch(release["url"], destination=archive)
        if archive.stat().st_size != release["size"]:
            raise UpdateError("invalid_package", "Incomplete download")
        digest = release["digest"]
        if digest and hashlib.sha256(archive.read_bytes()).hexdigest() != digest.split(":", 1)[1]:
            raise UpdateError("invalid_package", "Checksum mismatch")
        _write_result(directory, {"state": "ready", "version": release["version"]})
    except HTTPError as exc:
        code = "rate_limit" if exc.code in (403, 429) else "no_release" if exc.code == 404 else "network_error"
        _write_result(directory, {"state": "error", "code": code})
    except (URLError, TimeoutError, OSError):
        _write_result(directory, {"state": "error", "code": "network_error"})
    except UpdateError as exc:
        _write_result(directory, {"state": "error", "code": exc.code})
    except (ValueError, TypeError):
        _write_result(directory, {"state": "error", "code": "invalid_release"})


class UpdateJob:
    def __init__(self, current_version):
        self.directory = Path(tempfile.mkdtemp(prefix="node-console-download-"))
        self.started = time.monotonic()
        self.process = None
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-I", str(Path(__file__).resolve()), "--download", str(self.directory), current_version],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            atexit.register(self.close)
        except Exception:
            self.close()
            raise

    def poll(self):
        running = self.process.poll() is None
        if running and time.monotonic() - self.started > JOB_TIMEOUT:
            return {"state": "error", "code": "network_error"}
        path = self.directory / "result.json"
        result = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"state": "checking"}
        # Wait for process exit before touching or removing its files.
        if running and result["state"] in {"ready", "error", "current"}:
            return {"state": "checking"}
        if not running and (self.process.returncode != 0 or result["state"] in {"checking", "downloading"}):
            return {"state": "error", "code": "network_error"}
        return result

    def close(self):
        atexit.unregister(self.close)
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        shutil.rmtree(self.directory, ignore_errors=True)


def validate_target(target):
    target = Path(target)
    if target.is_symlink() or not (target / "__init__.py").is_file():
        raise UpdateError("unsafe_install")
    if any((parent / ".git").exists() for parent in (target, *target.parents)):
        raise UpdateError("development_install")
    if not os.access(target.parent, os.W_OK) or not os.access(target, os.W_OK):
        raise UpdateError("permission_error")


def _package_files(archive_path, expected_version, blender_version):
    files = {}
    seen = set()
    with ZipFile(archive_path) as archive:
        items = archive.infolist()
        if len(items) > 1000 or sum(item.file_size for item in items) > MAX_UNPACKED:
            raise UpdateError("invalid_package")
        for item in items:
            path = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (not path.parts or path.parts[0] != "Node_Console" or "\\" in item.filename
                    or any(part.startswith(".") or part == "__pycache__" or ":" in part
                           or part.endswith((" ", ".")) or any(ord(char) < 32 for char in part)
                           or part.split(".")[0].upper() in WINDOWS_DEVICE_NAMES
                           for part in path.parts)
                    or stat.S_ISLNK(mode) or item.flag_bits & 1):
                raise UpdateError("invalid_package", "Unsafe ZIP entry")
            key = str(path).casefold()
            if key in seen:
                raise UpdateError("invalid_package", "Duplicate ZIP entry")
            seen.add(key)
            if item.is_dir():
                continue
            relative = Path(*path.parts[1:])
            if (len(path.parts) < 2 or relative.name in PROTECTED_NAMES
                    or (relative.suffix not in {".py", ".json", ".md", ".txt"} and relative.name != "LICENSE")):
                raise UpdateError("invalid_package", "Unexpected package content")
            content = archive.read(item)
            if relative.suffix == ".py":
                ast.parse(content, filename=str(relative))
            files[relative] = content
    if not REQUIRED_FILES.issubset({str(path) for path in files}):
        raise UpdateError("invalid_package", "Missing add-on files")
    values = {}
    for node in ast.parse(files[Path("__init__.py")]).body:
        if isinstance(node, ast.Assign):
            for name in node.targets:
                if isinstance(name, ast.Name) and name.id in {"bl_info", "ADDON_VERSION"}:
                    values[name.id] = ast.literal_eval(node.value)
    info = values.get("bl_info", {})
    if (not isinstance(info, dict) or info.get("name") != "Node Console"
            or tuple(info.get("version", ())) != version_tuple(expected_version)
            or version_tuple(values.get("ADDON_VERSION")) != version_tuple(expected_version)):
        raise UpdateError("invalid_package", "Package/version mismatch")
    minimum = info.get("blender")
    if not isinstance(minimum, tuple) or len(minimum) != 3 or any(type(value) is not int for value in minimum):
        raise UpdateError("invalid_package")
    if tuple(blender_version) < minimum:
        raise UpdateError("incompatible_blender", ".".join(map(str, minimum)))
    return files


def install_release(archive, target, expected_version, blender_version, protected_paths=(), current_version=None):
    """Stage beside the installation, preserve local data, and keep a recovery copy.

    Loaded modules remain untouched until Blender restarts. No add-on/keymap reload.
    """
    target = Path(target)
    validate_target(target)
    installed_version = next((ast.literal_eval(node.value) for node in ast.parse((target / "__init__.py").read_bytes()).body
                              if isinstance(node, ast.Assign) and any(isinstance(name, ast.Name) and name.id == "ADDON_VERSION" for name in node.targets)), None)
    if ((current_version is not None and installed_version != current_version)
            or version_tuple(expected_version) <= version_tuple(installed_version)):
        raise UpdateError("changed_install")
    try:
        files = _package_files(archive, expected_version, blender_version)
    except UpdateError:
        raise
    except (BadZipFile, ValueError, TypeError, SyntaxError, KeyError, RuntimeError) as exc:
        raise UpdateError("invalid_package") from exc
    protected = {Path(path).resolve() for path in protected_paths}
    for path in files:
        if (target / path).resolve() in protected:
            raise UpdateError("protected_data")
    work = Path(tempfile.mkdtemp(prefix=".node-console-update-", dir=target.parent))
    staged, backup = work / "new", work / "previous"
    try:
        shutil.copytree(target, staged, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for relative, content in files.items():
            output = staged / relative
            if any((staged / Path(*relative.parts[:index])).is_symlink() for index in range(1, len(relative.parts) + 1)):
                raise UpdateError("unsafe_install")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)
        # Both renames are on the same filesystem; rollback if the second fails.
        target.rename(backup)
        try:
            staged.rename(target)
        except OSError:
            backup.rename(target)
            raise
    except Exception:
        if not backup.exists():
            shutil.rmtree(work, ignore_errors=True)
        raise
    return backup


if __name__ == "__main__" and len(sys.argv) == 4 and sys.argv[1] == "--download":
    download_release(Path(sys.argv[2]), sys.argv[3])
