"""Interactive disposable scene; launched only via run_windows_ime_lab.py."""
import importlib.util
import os
from pathlib import Path
import sys

import bpy


assert sys.platform == "win32" and "--factory-startup" in sys.argv
root = Path(__file__).resolve().parents[1]
lab = Path(os.environ["NC_WINDOWS_IME_LAB"]).resolve()
assert Path(os.environ["BLENDER_USER_CONFIG"]).resolve().parent == lab
spec = importlib.util.spec_from_file_location("NodeConsoleWindowsLab", root / "__init__.py",
                                            submodule_search_locations=[str(root)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._settings_path = lambda: lab / "settings.json"
nc._snippets_path = lambda: lab / "snippets.json"
nc.register()
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
area = max(bpy.context.screen.areas, key=lambda item: item.width * item.height)
area.type = "NODE_EDITOR"
area.ui_type = "GeometryNodeTree"
tree = bpy.data.node_groups.new("Node Console Windows IME Test", "GeometryNodeTree")
bpy.context.active_object.modifiers.new("IME Test", "NODES").node_group = tree
area.spaces.active.pin = True
area.spaces.active.node_tree = tree
tree.nodes.new("ShaderNodeTexNoise").location = (-300, 100)
tree.nodes.new("NodeGroupOutput").location = (100, 100)
print("Node Console Windows IME lab ready:", nc.ADDON_VERSION, bpy.app.version_string, flush=True)
print("Focus the node editor, press Shift+A and use Microsoft Pinyin. No input text is logged.", flush=True)
