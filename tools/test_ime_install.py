"""Exercise the staged macOS package in factory Blender with private config."""
import ctypes
import importlib
import os
from pathlib import Path
import sys

import addon_utils
import bpy


target = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
assert target.name == "Node_Console"
config = Path(os.environ["BLENDER_USER_CONFIG"]).resolve()
assert config.name == "test-config" and config.parent == target.parent
sys.path.insert(0, str(target.parent))
module = importlib.import_module("Node_Console")
assert Path(module.__file__).resolve().parent == target
module.__time__ = (target / "__init__.py").stat().st_mtime
original_invoke = module.ENS_AddNodeByEnglishSearch.invoke
from Node_Console.ime_input.library import materialize
library = ctypes.CDLL(str(materialize(cache=target.parent / "native-cache")))
assert library.nc_ime_focused() == 0
for _ in range(3):
    errors = []
    loaded = addon_utils.enable("Node_Console", default_set=True, handle_error=errors.append)
    assert loaded is module and not errors, errors
    assert callable(module.IME_UNINSTALL)
    assert module.ENS_AddNodeByEnglishSearch.invoke is not original_invoke
    assert Path(module._settings_path()).parent == config
    addon_utils.disable("Node_Console", default_set=True, handle_error=errors.append)
    assert not errors, errors
    assert module.IME_UNINSTALL is None
    assert module.ENS_AddNodeByEnglishSearch.invoke is original_invoke
    assert library.nc_ime_focused() == 0
print("IME_INSTALL_SMOKE_OK", bpy.app.version_string, "3 enable/disable cycles", flush=True)
