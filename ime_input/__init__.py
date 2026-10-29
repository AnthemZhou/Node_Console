"""Optional native IME support; other platforms retain the existing input path."""
import importlib
import sys

# Blender can reload only the package root after a manual installation.
for _name in ("session", "library", "adapter"):
    if _name in globals():
        importlib.reload(globals()[_name])


def install_if_available(module):
    if sys.platform != "darwin":
        return None
    from .adapter import install
    from .library import materialize

    def log(kind, **details):
        # Never log search terms or composition text in the distributed add-on.
        if kind == "ime_error":
            print("Node Console IME unavailable; using standard input:", details.get("message", ""))

    return install(module, materialize, log)
