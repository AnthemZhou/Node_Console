"""Bounded JSON snapshots and atomic writes for local user data."""
from copy import deepcopy
import json
import os
from pathlib import Path
import stat
import tempfile


class JsonStore:
    """Keep one file snapshot; callers never receive mutable cached values."""

    def __init__(self):
        self.revision = 0
        self.clear()

    def clear(self):
        self._stamp = None
        self._data = {}
        self._error = None
        self.revision += 1

    @staticmethod
    def _file_stamp(path):
        try:
            info = path.stat()
        except FileNotFoundError:
            return (path, None)
        return (path, info.st_dev, info.st_ino, info.st_size,
                info.st_mtime_ns, info.st_ctime_ns)

    def refresh(self, path):
        path = Path(path).resolve()
        try:
            stamp = self._file_stamp(path)
            if stamp == self._stamp:
                return self.revision
            data = {}
            if stamp[1] is not None:
                with path.open(encoding="utf-8") as stream:
                    data = json.load(stream)
                if not isinstance(data, dict):
                    raise ValueError("Expected a JSON object")
            # Do not publish a snapshot if another process changed the file mid-read.
            if self._file_stamp(path) != stamp:
                raise OSError("File changed while reading")
        except (OSError, ValueError) as exc:
            self.clear()
            self._error = exc
        else:
            self._data = data
            self._stamp = stamp
            self._error = None
            self.revision += 1
        return self.revision

    def read(self, path, key=None, default=None, *, project=None):
        """Copy a requested value; optional projections must not mutate their input."""
        self.refresh(path)
        value = self._data
        if key is not None:
            for part in key if isinstance(key, tuple) else (key,):
                if not isinstance(value, dict) or part not in value:
                    value = default
                    break
                value = value[part]
        if project is not None:
            value = project(value)
        return deepcopy(value)

    def write(self, path, data):
        path = Path(path).resolve()
        self.refresh(path)
        if self._error is not None:
            raise OSError(f"Cannot safely replace unreadable JSON: {path}") from self._error
        original_stamp = self._stamp
        content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             prefix=f".{path.name}.", suffix=".tmp",
                                             delete=False) as stream:
                pending = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            if original_stamp[1] is not None:
                pending.chmod(stat.S_IMODE(path.stat().st_mode))
            if self._file_stamp(path) != original_stamp:
                raise OSError("File changed while saving; retry the operation")
            os.replace(pending, path)
        finally:
            if pending is not None:
                pending.unlink(missing_ok=True)
            self.clear()
