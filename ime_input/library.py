"""Verify and materialize the bundled library, without downloads or compilation.

JSON packaging keeps upgrades compatible with the 1.3.x updater's file whitelist.
SHA256 detects corruption; it is not a substitute for trusting the release source.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


RESOURCE = Path(__file__).with_name("macos.json")


def materialize(resource=RESOURCE, cache=None):
    payload = json.loads(resource.read_text(encoding="utf-8"))
    version = payload["version"]
    if payload.get("format") != 1 or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Unsupported native input resource")
    data = base64.b64decode(payload["data"], validate=True)
    digest = hashlib.sha256(data).hexdigest()
    if digest != payload["sha256"] or data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("Invalid native input library checksum or format")
    cache = Path(cache) if cache is not None else Path.home() / "Library/Caches/NodeConsole/IME"
    directory = cache / digest
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / ("nc_ime_" + version.replace(".", "_") + ".dylib")
    if target.is_file() and not target.is_symlink() and hashlib.sha256(target.read_bytes()).hexdigest() == digest:
        return target
    fd, pending = tempfile.mkstemp(prefix=".native-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(pending, 0o700)
        os.replace(pending, target)
    finally:
        if os.path.exists(pending):
            os.unlink(pending)
    return target
