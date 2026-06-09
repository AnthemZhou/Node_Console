from __future__ import annotations

import ast
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import blf
import bpy
import gpu
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import AddonPreferences, Operator, SpaceNodeEditor
from gpu_extras.batch import batch_for_shader


bl_info = {
    "name": "Node Console",
    "author": "Anthem",
    "version": (0, 7, 2),
    "blender": (4, 0, 0),
    "location": "Node Editor > Shift A",
    "description": "Language-independent custom node launcher with favorite boosting.",
    "category": "Node",
}


ADDON_ID = __name__
KEYMAP_ITEMS = []
NODE_SEARCH_ENTRIES: list["NodeSearchEntry"] = []

FONT_ID = 0
MAX_RESULTS = 12
PANEL_WIDTH = 430
SEARCH_HEIGHT = 31
ROW_HEIGHT = 26
PANEL_PADDING = 8
SHORTCUT_HEIGHT = 30
SHORTCUT_GAP = 6
CONTEXT_MENU_WIDTH = 190
CONTEXT_MENU_ROW_HEIGHT = 30
PANEL_BACKGROUND = (0.095, 0.095, 0.1, 0.98)
FIELD_BACKGROUND = (0.12, 0.12, 0.125, 1.0)
BORDER_COLOR = (0.24, 0.24, 0.25, 0.92)
HIGHLIGHT_COLOR = (0.31, 0.31, 0.31, 0.98)
HIGHLIGHT_BORDER_COLOR = (0.38, 0.38, 0.38, 0.85)
TEXT_COLOR = (0.88, 0.88, 0.9, 1.0)
MUTED_TEXT_COLOR = (0.58, 0.58, 0.6, 1.0)
SETTINGS_FILENAME = "node_console_settings.json"


@dataclass(frozen=True)
class NodeSearchEntry:
    identifier: str
    category: str
    english: str
    chinese: str
    label: str
    description: str
    kind: str
    node_type: str = ""
    asset_path: str = ""
    asset_name: str = ""
    search_text: str = ""
    settings: tuple[tuple[str, str], ...] = ()


NODE_ENTRY_BY_ID: dict[str, NodeSearchEntry] = {}


def _safe_identifier(prefix: str, *parts: str) -> str:
    text = "_".join(part for part in parts if part)
    text = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")
    return f"{prefix}_{text[:80]}"


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", " ", text.lower()).replace("_", " ").strip()


def _camel_words(text: str) -> str:
    text = re.sub(r"(Node|Shader|Function|Geometry|Compositor|Texture)", " ", text)
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return _normalize(text)


def _compact(text: str) -> str:
    return _normalize(text).replace(" ", "")


def _preferences():
    addon = bpy.context.preferences.addons.get(ADDON_ID)
    return addon.preferences if addon else None


def _settings_path() -> Path:
    try:
        config_dir = bpy.utils.user_resource("CONFIG", path="", create=True)
    except Exception:
        config_dir = str(Path.home())
    return Path(config_dir) / SETTINGS_FILENAME


def _load_settings() -> dict:
    path = _settings_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def _write_settings(data: dict):
    path = _settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass


def _save_preference_settings():
    prefs = _preferences()
    if not prefs:
        return

    data = _load_settings()
    data.update(
        {
            "display_mode": prefs.display_mode,
            "ui_scale": prefs.ui_scale,
            "shortcut_key": prefs.shortcut_key,
            "shortcut_shift": prefs.shortcut_shift,
            "shortcut_ctrl": prefs.shortcut_ctrl,
            "shortcut_alt": prefs.shortcut_alt,
            "settings_version": 2,
        }
    )
    _write_settings(data)


def _load_preferences_from_settings():
    prefs = _preferences()
    if not prefs:
        return

    data = _load_settings()
    if data.get("settings_version", 1) < 2 and isinstance(data.get("ui_scale"), (int, float)):
        data["ui_scale"] = max(1.0, min(2.0, float(data["ui_scale"]) / 1.7))
        data["settings_version"] = 2
        _write_settings(data)
    for name in ("display_mode", "ui_scale", "shortcut_key", "shortcut_shift", "shortcut_ctrl", "shortcut_alt"):
        if name in data:
            try:
                setattr(prefs, name, data[name])
            except Exception:
                pass


def _ui_scale() -> float:
    prefs = _preferences()
    if not prefs:
        return 1.7
    return max(1.0, min(2.0, prefs.ui_scale)) * 1.7


def _scaled(value: float, scale: float) -> float:
    return round(value * scale)


def _load_string_list(name: str) -> list[str]:
    raw = _load_settings().get(name, [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def _save_string_list(name: str, values: list[str]):
    data = _load_settings()
    data[name] = values
    _write_settings(data)


def _load_favorites() -> set[str]:
    return set(_load_string_list("favorites"))


def _load_shortcuts() -> list[str]:
    seen = set()
    shortcuts = []
    for identifier in _load_string_list("shortcuts"):
        if identifier not in seen:
            shortcuts.append(identifier)
            seen.add(identifier)
    return shortcuts


def _load_favorite_meta() -> dict[str, str]:
    raw = _load_settings().get("favorite_meta", {})
    if not isinstance(raw, dict):
        return {}
    return {key: value for key, value in raw.items() if isinstance(key, str) and isinstance(value, str)}


def _save_favorites(favorites: set[str], favorite_meta: dict[str, str] | None = None):
    data = _load_settings()
    data["favorites"] = sorted(favorites)
    if favorite_meta is not None:
        data["favorite_meta"] = {key: favorite_meta[key] for key in sorted(favorite_meta)}
    _write_settings(data)


def _save_shortcuts(shortcuts: list[str]):
    _save_string_list("shortcuts", shortcuts)


def _add_shortcut(identifier: str):
    shortcuts = _load_shortcuts()
    if identifier not in shortcuts:
        shortcuts.append(identifier)
        _save_shortcuts(shortcuts)


def _remove_shortcut(identifier: str):
    _save_shortcuts([item for item in _load_shortcuts() if item != identifier])


def _move_shortcut(identifier: str, delta: int):
    shortcuts = _load_shortcuts()
    if identifier not in shortcuts:
        return
    index = shortcuts.index(identifier)
    new_index = max(0, min(len(shortcuts) - 1, index + delta))
    if new_index == index:
        return
    shortcuts.insert(new_index, shortcuts.pop(index))
    _save_shortcuts(shortcuts)


def _remove_favorite(identifier: str):
    favorites = _load_favorites()
    favorite_meta = _load_favorite_meta()
    favorites.discard(identifier)
    favorite_meta.pop(identifier, None)
    _save_favorites(favorites, favorite_meta)


def _preference_changed(_self, _context):
    _save_preference_settings()


def _shortcut_changed(_self, _context):
    _save_preference_settings()
    refresh_keymap()


def _translation_label(text: str) -> str:
    if not text:
        return text

    for translate in (
        getattr(bpy.app.translations, "pgettext_iface", None),
        getattr(bpy.app.translations, "pgettext_data", None),
    ):
        if not translate:
            continue

        try:
            translated = translate(text)
        except Exception:
            continue

        if translated and translated != text:
            return translated

    return text


def _entry_label(english: str, chinese: str) -> str:
    prefs = _preferences()
    display_mode = prefs.display_mode if prefs else "ENGLISH_CHINESE"

    if display_mode == "ENGLISH":
        return english
    if display_mode == "CHINESE" and chinese != english:
        return chinese
    if display_mode == "CHINESE_ENGLISH" and chinese != english:
        return f"{chinese} / {english}"
    if chinese != english:
        return f"{english} / {chinese}"

    return english


def _node_tree_allows_node(context, node_type: str) -> bool:
    space = context.space_data
    node_tree = getattr(space, "edit_tree", None)
    if not node_tree:
        return False

    bl_rna = bpy.types.Node.bl_rna_get_subclass(node_type)
    if bl_rna is None:
        return False

    node_cls = getattr(bpy.types, node_type, None)
    if node_cls is None:
        return True

    poll = getattr(node_cls, "poll", None)
    if not poll:
        return True

    try:
        return bool(poll(node_tree))
    except Exception:
        return True


def _iter_node_classes():
    pending = list(bpy.types.Node.__subclasses__())
    seen = set()

    while pending:
        cls = pending.pop()
        if cls in seen:
            continue

        seen.add(cls)
        pending.extend(cls.__subclasses__())

        bl_idname = getattr(cls, "bl_idname", "")
        bl_label = getattr(cls, "bl_label", "")
        if bl_idname and bl_label:
            yield cls


def _node_menu_script_paths() -> list[Path]:
    paths = []

    for resource_type in ("LOCAL", "SYSTEM", "USER"):
        try:
            resource_path = Path(bpy.utils.resource_path(resource_type))
        except Exception:
            continue

        ui_path = resource_path / "scripts/startup/bl_ui"
        if ui_path.exists():
            paths.extend(sorted(ui_path.glob("node_add_menu*.py")))

    return paths


def _constant_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _category_from_class_name(name: str) -> str:
    text = name
    for prefix in ("NODE_MT_gn_", "NODE_MT_shader_node_", "NODE_MT_compositor_node_", "NODE_MT_texture_node_", "NODE_MT_category_"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    text = re.sub(r"_base$", "", text)
    tokens = [token for token in text.split("_") if token not in {"node", "nodes", "all", "category"}]
    if not tokens:
        return "Node"

    labels = {
        "gn": "Geometry",
        "uv": "UV",
    }
    return " > ".join(labels.get(token, token.replace("and", "&").title()) for token in tokens)


def _enum_items_for_node_property(node_type: str, property_name: str):
    node_cls = getattr(bpy.types, node_type, None)
    if not node_cls:
        return

    try:
        prop = node_cls.bl_rna.properties[property_name]
    except Exception:
        return

    translation_context = getattr(prop, "translation_context", None)
    for item in prop.enum_items_static:
        english = item.name
        chinese = english
        if translation_context:
            try:
                translated = bpy.app.translations.pgettext_iface(english, translation_context)
                if translated:
                    chinese = translated
            except Exception:
                pass
        yield item.identifier, english, chinese


def _iter_menu_entries():
    seen = set()

    for path in _node_menu_script_paths():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            category = _category_from_class_name(class_node.name)

            for node in ast.walk(class_node):
                if not isinstance(node, ast.Call):
                    continue

                func = node.func
                if not isinstance(func, ast.Attribute):
                    continue

                if func.attr == "add_color_mix_node":
                    key = ("ShaderNodeMix", (), category)
                    if key not in seen:
                        seen.add(key)
                        yield "ShaderNodeMix", category, "", ()
                    for item_identifier, item_english, item_chinese in _enum_items_for_node_property("ShaderNodeMix", "blend_type"):
                        settings = (("blend_type", item_identifier),)
                        key = ("ShaderNodeMix", settings, category)
                        if key in seen:
                            continue
                        seen.add(key)
                        yield "ShaderNodeMix", category, item_english, settings
                    continue

                if func.attr not in {"node_operator", "node_operator_with_outputs", "node_operator_with_searchable_enum"}:
                    continue

                candidates = [_constant_string(arg) for arg in node.args]
                node_type = next((candidate for candidate in candidates if candidate and "Node" in candidate), None)
                if not node_type:
                    continue

                key = (node_type, (), category)
                if key not in seen:
                    seen.add(key)
                    yield node_type, category, "", ()

                if func.attr != "node_operator_with_searchable_enum":
                    continue

                property_name = next(
                    (
                        candidate
                        for candidate in candidates
                        if candidate and candidate != node_type and "Node" not in candidate
                    ),
                    "",
                )
                if not property_name:
                    continue

                for item_identifier, item_english, item_chinese in _enum_items_for_node_property(node_type, property_name):
                    settings = ((property_name, item_identifier),)
                    key = (node_type, settings, category)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield node_type, category, item_english, settings


def _asset_node_directories() -> list[Path]:
    directories = []

    for resource_type in ("LOCAL", "SYSTEM", "USER"):
        try:
            resource_path = Path(bpy.utils.resource_path(resource_type))
        except Exception:
            continue

        nodes_dir = resource_path / "datafiles/assets/nodes"
        if nodes_dir.exists():
            directories.append(nodes_dir)

    try:
        for library in bpy.context.preferences.filepaths.asset_libraries:
            library_path = Path(bpy.path.abspath(library.path))
            if library_path.exists():
                directories.append(library_path)
    except Exception:
        pass

    return directories


def _iter_asset_node_groups():
    seen = set()

    for nodes_dir in _asset_node_directories():
        for blend_path in sorted(nodes_dir.rglob("*.blend")):
            try:
                with bpy.data.libraries.load(str(blend_path), assets_only=True) as (data_from, _data_to):
                    names = list(getattr(data_from, "node_groups", ()))
            except TypeError:
                try:
                    with bpy.data.libraries.load(str(blend_path)) as (data_from, _data_to):
                        names = list(getattr(data_from, "node_groups", ()))
                except Exception:
                    continue
            except Exception:
                continue

            for name in names:
                key = (str(blend_path), name)
                if key in seen:
                    continue

                seen.add(key)
                yield blend_path, name


def _make_search_text(english: str, chinese: str, label: str, node_type: str) -> str:
    node_words = _camel_words(node_type)
    node_without_suffix = re.sub(r"Node$", "", node_type)
    pieces = [
        english,
        chinese,
        label,
        node_type,
        node_words,
        _camel_words(node_without_suffix),
        english.replace(" ", ""),
        chinese.replace(" ", ""),
        node_words.replace(" ", ""),
        node_without_suffix,
    ]
    return _normalize(" ".join(piece for piece in pieces if piece))


def _rebuild_search_entries(context):
    NODE_SEARCH_ENTRIES.clear()
    NODE_ENTRY_BY_ID.clear()

    seen_keys = set()

    def add_entry(entry: NodeSearchEntry):
        NODE_SEARCH_ENTRIES.append(entry)
        NODE_ENTRY_BY_ID[entry.identifier] = entry

    def add_builtin_entry(node_type: str, category: str = "Node", variant_label: str = "", settings=(), trusted_menu=False):
        key = (node_type, tuple(settings))
        if key in seen_keys:
            return
        if not trusted_menu and not _node_tree_allows_node(context, node_type):
            return

        seen_keys.add(key)

        bl_rna = bpy.types.Node.bl_rna_get_subclass(node_type)
        base_english = bl_rna.name if bl_rna and bl_rna.name else node_type
        english = f"{base_english} > {variant_label}" if variant_label else base_english
        chinese = _translation_label(english)
        label = _entry_label(english, chinese)
        description = bl_rna.description if bl_rna and bl_rna.description else english
        identifier = _safe_identifier("N", node_type, english, repr(settings))
        add_entry(
            NodeSearchEntry(
                identifier=identifier,
                category=category,
                english=english,
                chinese=chinese,
                label=label,
                description=description,
                kind="NODE",
                node_type=node_type,
                search_text=_make_search_text(english, chinese, label, node_type),
                settings=tuple(settings),
            )
        )

    for node_type, category, variant_label, settings in _iter_menu_entries():
        add_builtin_entry(node_type, category, variant_label, settings, trusted_menu=True)

    for cls in sorted(_iter_node_classes(), key=lambda item: getattr(item, "bl_label", "")):
        add_builtin_entry(cls.bl_idname)

    space = context.space_data
    edit_tree = getattr(space, "edit_tree", None)
    if edit_tree and edit_tree.bl_idname == "GeometryNodeTree":
        for blend_path, asset_name in _iter_asset_node_groups():
            chinese = _translation_label(asset_name)
            label = _entry_label(asset_name, chinese)
            description = f"Node group asset: {asset_name}"
            identifier = _safe_identifier("A", asset_name, str(blend_path))
            add_entry(
                NodeSearchEntry(
                    identifier=identifier,
                    category="Asset",
                    english=asset_name,
                    chinese=chinese,
                    label=label,
                    description=description,
                    kind="ASSET",
                    asset_path=str(blend_path),
                    asset_name=asset_name,
                    search_text=_make_search_text(asset_name, chinese, label, ""),
                )
            )


def _score_entry(entry: NodeSearchEntry, query: str, favorites: set[str]) -> int | None:
    query = _normalize(query)
    if not query:
        return None

    text = entry.search_text
    compact_text = text.replace(" ", "")
    compact_query = query.replace(" ", "")
    tokens = query.split()

    if all(token in text for token in tokens):
        score = 100
    elif compact_query and compact_query in compact_text:
        score = 80
    else:
        if len(compact_query) < 3:
            return None
        position = 0
        score = 0
        total_gap = 0
        for char in compact_query:
            found = compact_text.find(char, position)
            if found < 0:
                return None
            gap = found - position
            total_gap += max(0, gap)
            score += max(1, 12 - gap)
            position = found + 1
        if total_gap > len(compact_query) * 3:
            return None

    english = _normalize(entry.english)
    chinese = _normalize(entry.chinese)
    if english == query:
        score += 1000
    elif chinese == query:
        score += 1000
    elif english.startswith(query):
        score += 450
    elif chinese.startswith(query):
        score += 450
    elif query in english:
        score += 250
    elif query in chinese:
        score += 250

    if entry.identifier in favorites:
        score += 2000

    return score


def _search_entries(query: str, favorites: set[str]) -> list[NodeSearchEntry]:
    scored = []

    for index, entry in enumerate(NODE_SEARCH_ENTRIES):
        score = _score_entry(entry, query, favorites)
        if score is None:
            continue
        scored.append((score, entry.identifier in favorites, entry.english.lower(), index, entry))

    scored.sort(key=lambda item: (-item[0], not item[1], item[2], item[3]))
    return [item[-1] for item in scored]


def _store_cursor_location(context, event):
    space = context.space_data
    if not space or not getattr(space, "edit_tree", None):
        return

    if context.region and context.region.type == "WINDOW":
        area = context.area
        horizontal_pad = int(area.width / 10)
        vertical_pad = int(area.height / 10)
        x = min(max(horizontal_pad, event.mouse_region_x), area.width - horizontal_pad)
        y = min(max(vertical_pad, event.mouse_region_y), area.height - vertical_pad)
        space.cursor_location_from_region(x, y)
    else:
        space.cursor_location = space.edit_tree.view_center


def _add_builtin_node(context, entry: NodeSearchEntry):
    space = context.space_data
    edit_tree = space.edit_tree

    try:
        node = edit_tree.nodes.new(type=entry.node_type)
    except RuntimeError as ex:
        raise RuntimeError(str(ex)) from ex

    for selected_node in edit_tree.nodes:
        selected_node.select = False

    node.location = space.cursor_location
    node.select = True
    edit_tree.nodes.active = node
    _apply_node_settings(node, entry.settings)

    return node


def _apply_node_settings(node, settings: tuple[tuple[str, str], ...]):
    for name, value in settings:
        try:
            if name.startswith("inputs["):
                continue
            setattr(node, name, value)
        except Exception:
            pass


def _load_asset_node_group(entry: NodeSearchEntry):
    existing = bpy.data.node_groups.get(entry.asset_name)
    if existing:
        return existing

    try:
        with bpy.data.libraries.load(entry.asset_path, link=False, assets_only=True) as (_data_from, data_to):
            data_to.node_groups = [entry.asset_name]
    except TypeError:
        with bpy.data.libraries.load(entry.asset_path, link=False) as (_data_from, data_to):
            data_to.node_groups = [entry.asset_name]

    return bpy.data.node_groups.get(entry.asset_name)


def _add_asset_node(context, entry: NodeSearchEntry):
    node_group = _load_asset_node_group(entry)
    if not node_group:
        return None

    space = context.space_data
    edit_tree = space.edit_tree

    from nodeitems_builtins import node_tree_group_type

    node_type = node_tree_group_type.get(edit_tree.bl_idname, "GeometryNodeGroup")
    node = edit_tree.nodes.new(type=node_type)
    node.node_tree = node_group

    for selected_node in edit_tree.nodes:
        selected_node.select = False

    node.location = space.cursor_location
    node.select = True
    edit_tree.nodes.active = node

    return node


def _draw_rect(x: float, y: float, width: float, height: float, color: tuple[float, float, float, float]):
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    vertices = ((x, y), (x + width, y), (x + width, y + height), (x, y + height))
    batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _rounded_rect_vertices(x: float, y: float, width: float, height: float, radius: float, segments: int = 8):
    radius = max(0, min(radius, width / 2, height / 2))
    corners = (
        (x + width - radius, y + height - radius, 0, math.pi / 2),
        (x + radius, y + height - radius, math.pi / 2, math.pi),
        (x + radius, y + radius, math.pi, math.pi * 1.5),
        (x + width - radius, y + radius, math.pi * 1.5, math.pi * 2),
    )
    vertices = [(x + width / 2, y + height / 2)]

    for cx, cy, start, end in corners:
        for step in range(segments + 1):
            angle = start + (end - start) * (step / segments)
            vertices.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))

    vertices.append(vertices[1])
    return vertices


def _draw_rounded_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
    color: tuple[float, float, float, float],
):
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    batch = batch_for_shader(shader, "TRI_FAN", {"pos": _rounded_rect_vertices(x, y, width, height, radius)})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_rounded_panel(
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
    fill: tuple[float, float, float, float],
    border: tuple[float, float, float, float] = BORDER_COLOR,
):
    _draw_rounded_rect(x, y, width, height, radius, border)
    _draw_rounded_rect(x + 1, y + 1, width - 2, height - 2, max(0, radius - 1), fill)


def _draw_text(text: str, x: float, y: float, size: int, color: tuple[float, float, float, float]):
    blf.size(FONT_ID, size)
    blf.color(FONT_ID, *color)
    blf.position(FONT_ID, x, y, 0)
    blf.draw(FONT_ID, text)


def _text_width(text: str, size: int) -> float:
    blf.size(FONT_ID, size)
    return blf.dimensions(FONT_ID, text)[0]


def _abbreviate_label(label: str, max_chars: int = 12) -> str:
    label = label.split(" / ")[0].split(" > ")[0].strip()
    if len(label) <= max_chars:
        return label

    words = label.split()
    if len(words) >= 2:
        first = words[0][:4]
        last = words[-1][: max(3, max_chars - len(first) - 2)]
        return f"{first}. {last}"

    return f"{label[: max_chars - 1]}."


def _fit_text(text: str, max_width: float, size: int) -> str:
    if _text_width(text, size) <= max_width:
        return text
    ellipsis = "."
    trimmed = text
    while trimmed and _text_width(trimmed + ellipsis, size) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + ellipsis) if trimmed else ellipsis


class ENS_AddNodeByEnglishSearch(Operator):
    bl_idname = "node.node_console"
    bl_label = "Node Console"
    bl_description = "Search and add nodes by English name"
    bl_options = {"REGISTER", "UNDO"}

    _draw_handler = None
    _query = ""
    _selected_index = 0
    _results: list[NodeSearchEntry] = []
    _favorites: set[str] = set()
    _favorite_meta: dict[str, str] = {}
    _panel_rect = (0, 0, 0, 0)
    _rows_top = 0
    _row_height = ROW_HEIGHT
    _padding = PANEL_PADDING
    _search_height = SEARCH_HEIGHT
    _context_menu_index = None
    _context_menu_rect = (0, 0, 0, 0)
    _context_menu_hover = None
    _anchor_x = 0
    _anchor_y = 0
    _panel_x = None
    _search_y = None
    _placing_node = None
    _scroll_offset = 0
    _visible_limit = MAX_RESULTS
    _shortcuts: list[str] = []
    _shortcut_rects: list[tuple[str, tuple[float, float, float, float]]] = []
    _shortcut_hover = None

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return (
            space
            and space.type == "NODE_EDITOR"
            and getattr(space, "edit_tree", None)
            and space.edit_tree.is_editable
        )

    def _refresh_results(self):
        self._results = _search_entries(self._query, self._favorites)
        self._context_menu_index = None
        self._scroll_offset = min(self._scroll_offset, max(0, len(self._results) - 1))
        if not self._results:
            self._selected_index = 0
            return
        self._selected_index = max(0, min(self._selected_index, len(self._results) - 1))

    def _finish(self, context, result):
        if self._draw_handler is not None:
            SpaceNodeEditor.draw_handler_remove(self._draw_handler, "WINDOW")
            self._draw_handler = None
        self._placing_node = None
        if context.area:
            context.area.tag_redraw()
        return result

    def _hide_console(self, context):
        if self._draw_handler is not None:
            SpaceNodeEditor.draw_handler_remove(self._draw_handler, "WINDOW")
            self._draw_handler = None
        if context.area:
            context.area.tag_redraw()

    def _move_placing_node(self, context, event):
        if not self._placing_node:
            return
        space = context.space_data
        if event and context.region and context.region.type == "WINDOW":
            space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        self._placing_node.location = space.cursor_location

    def _begin_placement(self, context, event, node):
        self._hide_console(context)
        self._placing_node = node
        self._move_placing_node(context, event)
        return {"RUNNING_MODAL"}

    def _cancel_placement(self, context):
        node = self._placing_node
        self._placing_node = None
        if node:
            try:
                node.id_data.nodes.remove(node)
            except Exception:
                pass
        return self._finish(context, {"CANCELLED"})

    def _confirm(self, context, event):
        if not self._results:
            return self._finish(context, {"CANCELLED"})

        entry = self._results[self._selected_index]
        if entry.kind == "NODE":
            try:
                node = _add_builtin_node(context, entry)
                return self._begin_placement(context, event, node)
            except RuntimeError as ex:
                self.report({"ERROR"}, str(ex))
                return self._finish(context, {"CANCELLED"})

        if entry.kind == "ASSET":
            result = _add_asset_node(context, entry)
            if result:
                return self._begin_placement(context, event, result)

            self.report({"ERROR"}, f"Unable to add asset node: {entry.asset_name}")
            return self._finish(context, {"CANCELLED"})

        return self._finish(context, {"CANCELLED"})

    def _row_index_from_mouse(self, event):
        x, y, width, height = self._panel_rect
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        rows_top = self._rows_top

        if mouse_x < x or mouse_x > x + width:
            return None
        if mouse_y > rows_top or mouse_y < y + self._padding:
            return None

        index = self._scroll_offset + int((rows_top - mouse_y) // self._row_height)
        if self._scroll_offset <= index < min(len(self._results), self._scroll_offset + self._visible_limit):
            return index
        return None

    def _shortcut_identifier_from_mouse(self, event):
        for identifier, rect in self._shortcut_rects:
            x, y, width, height = rect
            if x <= event.mouse_region_x <= x + width and y <= event.mouse_region_y <= y + height:
                return identifier
        return None

    def _update_shortcut_hover(self, event):
        self._shortcut_hover = self._shortcut_identifier_from_mouse(event)

    def _entry_from_identifier(self, identifier: str):
        return NODE_ENTRY_BY_ID.get(identifier)

    def _mouse_in_panel(self, event):
        x, y, width, height = self._panel_rect
        return x <= event.mouse_region_x <= x + width and y <= event.mouse_region_y <= y + height

    def _context_menu_action_from_mouse(self, event):
        x, y, width, height = self._context_menu_rect
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        if mouse_x < x or mouse_x > x + width or mouse_y < y or mouse_y > y + height:
            return None

        row = int((y + height - mouse_y) // (height / 4))
        return ("FAVORITE", "UNFAVORITE", "SHORTCUT", "UNSHORTCUT")[max(0, min(3, row))]

    def _update_context_menu_hover(self, event):
        self._context_menu_hover = self._context_menu_action_from_mouse(event)

    def _set_favorite(self, index, should_favorite: bool):
        if index is None or index >= len(self._results):
            return

        entry = self._results[index]
        identifier = entry.identifier
        if should_favorite:
            self._favorites.add(identifier)
            self._favorite_meta[identifier] = entry.label
        else:
            self._favorites.discard(identifier)
            self._favorite_meta.pop(identifier, None)
        _save_favorites(self._favorites, self._favorite_meta)
        self._refresh_results()

    def _open_context_menu(self, event, index):
        if index is None:
            return

        self._context_menu_index = index
        scale = _ui_scale()
        width = _scaled(CONTEXT_MENU_WIDTH, scale)
        row_height = _scaled(CONTEXT_MENU_ROW_HEIGHT, scale)
        x = event.mouse_region_x
        y = event.mouse_region_y - row_height * 4
        if self._panel_rect[2]:
            panel_x, panel_y, panel_width, panel_height = self._panel_rect
            x = min(max(panel_x, x), panel_x + panel_width - width)
            y = min(max(panel_y, y), panel_y + panel_height - row_height * 4)
        self._context_menu_rect = (x, y, width, row_height * 4)
        self._context_menu_hover = self._context_menu_action_from_mouse(event)

    def invoke(self, context, event):
        _store_cursor_location(context, event)
        _rebuild_search_entries(context)

        if not NODE_SEARCH_ENTRIES:
            self.report({"WARNING"}, "No addable nodes found for the current node tree")
            return {"CANCELLED"}

        self._query = ""
        self._selected_index = 0
        self._context_menu_index = None
        self._context_menu_hover = None
        self._anchor_x = event.mouse_region_x
        self._anchor_y = event.mouse_region_y
        self._panel_x = None
        self._search_y = None
        self._favorites = _load_favorites()
        self._favorite_meta = _load_favorite_meta()
        self._shortcuts = _load_shortcuts()
        self._scroll_offset = 0
        self._refresh_results()
        self._draw_handler = SpaceNodeEditor.draw_handler_add(self._draw_callback, (context,), "WINDOW", "POST_PIXEL")
        context.window_manager.modal_handler_add(self)
        if context.area:
            context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if self._placing_node:
            if event.type == "MOUSEMOVE":
                self._move_placing_node(context, event)
                if context.area:
                    context.area.tag_redraw()
                return {"RUNNING_MODAL"}

            if event.value == "PRESS":
                if event.type == "ESC":
                    return self._cancel_placement(context)
                if event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"}:
                    self._move_placing_node(context, event)
                    return self._finish(context, {"FINISHED"})

            return {"RUNNING_MODAL"}

        if event.value == "PRESS":
            if event.type in {"ESC"}:
                return self._finish(context, {"CANCELLED"})

            if event.type in {"RET", "NUMPAD_ENTER"}:
                if self._placing_node:
                    return self._finish(context, {"FINISHED"})
                return self._confirm(context, event)

            if event.type == "UP_ARROW":
                self._selected_index = max(0, self._selected_index - 1)
                self._scroll_offset = min(self._scroll_offset, self._selected_index)
            elif event.type == "DOWN_ARROW":
                self._selected_index = min(max(0, len(self._results) - 1), self._selected_index + 1)
                if self._selected_index >= self._scroll_offset + self._visible_limit:
                    self._scroll_offset = self._selected_index - self._visible_limit + 1
            elif event.type == "WHEELUPMOUSE":
                self._scroll_offset = max(0, self._scroll_offset - 1)
            elif event.type == "WHEELDOWNMOUSE":
                self._scroll_offset = min(max(0, len(self._results) - self._visible_limit), self._scroll_offset + 1)
            elif event.type == "BACK_SPACE":
                self._query = self._query[:-1]
                self._refresh_results()
            elif event.type == "DEL":
                self._query = ""
                self._refresh_results()
            elif event.type == "LEFTMOUSE":
                if self._context_menu_index is not None:
                    action = self._context_menu_action_from_mouse(event)
                    entry = self._results[self._context_menu_index] if self._context_menu_index < len(self._results) else None
                    if action == "FAVORITE":
                        self._set_favorite(self._context_menu_index, True)
                    elif action == "UNFAVORITE":
                        self._set_favorite(self._context_menu_index, False)
                    elif action == "SHORTCUT" and entry:
                        _add_shortcut(entry.identifier)
                        self._favorite_meta[entry.identifier] = entry.label
                        _save_favorites(self._favorites, self._favorite_meta)
                        self._shortcuts = _load_shortcuts()
                        self._context_menu_index = None
                        self._query = ""
                        self._scroll_offset = 0
                        self._refresh_results()
                    elif action == "UNSHORTCUT" and entry:
                        _remove_shortcut(entry.identifier)
                        self._shortcuts = _load_shortcuts()
                        self._context_menu_index = None
                    else:
                        self._context_menu_index = None
                        if not self._mouse_in_panel(event):
                            return self._finish(context, {"CANCELLED"})
                    if context.area:
                        context.area.tag_redraw()
                    return {"RUNNING_MODAL"}

                index = self._row_index_from_mouse(event)
                if index is not None:
                    self._selected_index = index
                    return self._confirm(context, event)
                shortcut_identifier = self._shortcut_identifier_from_mouse(event)
                if shortcut_identifier:
                    entry = self._entry_from_identifier(shortcut_identifier)
                    if entry:
                        self._results = [entry]
                        self._selected_index = 0
                        return self._confirm(context, event)
                if not self._mouse_in_panel(event):
                    return self._finish(context, {"CANCELLED"})
            elif event.type == "RIGHTMOUSE":
                self._open_context_menu(event, self._row_index_from_mouse(event))
            elif event.type == "MOUSEMOVE":
                if self._context_menu_index is not None:
                    self._update_context_menu_hover(event)
                    if context.area:
                        context.area.tag_redraw()
                    return {"RUNNING_MODAL"}

                index = self._row_index_from_mouse(event)
                if index is not None:
                    self._selected_index = index
                old_hover = self._shortcut_hover
                self._update_shortcut_hover(event)
                if old_hover != self._shortcut_hover and context.area:
                    context.area.tag_redraw()
            elif event.unicode and not event.ctrl and not event.alt and not event.oskey:
                self._query += event.unicode
                self._refresh_results()

            if context.area:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            if self._context_menu_index is not None:
                old_hover = self._context_menu_hover
                self._update_context_menu_hover(event)
                if old_hover != self._context_menu_hover and context.area:
                    context.area.tag_redraw()
                return {"RUNNING_MODAL"}

            index = self._row_index_from_mouse(event)
            if index is not None and index != self._selected_index:
                self._selected_index = index
                if context.area:
                    context.area.tag_redraw()
            old_hover = self._shortcut_hover
            self._update_shortcut_hover(event)
            if old_hover != self._shortcut_hover and context.area:
                context.area.tag_redraw()

        return {"RUNNING_MODAL"}

    def _draw_callback(self, context):
        region = context.region
        if not region:
            return

        scale = _ui_scale()
        padding = _scaled(PANEL_PADDING, scale)
        search_height = _scaled(SEARCH_HEIGHT, scale)
        row_height = _scaled(ROW_HEIGHT, scale)
        gap = _scaled(12, scale)
        shortcut_height = _scaled(SHORTCUT_HEIGHT, scale)
        shortcut_gap = _scaled(SHORTCUT_GAP, scale)
        radius = _scaled(5, scale)
        width = min(_scaled(PANEL_WIDTH, scale), region.width - _scaled(12, scale))
        has_query = bool(_normalize(self._query))
        search_width = width - padding * 2
        active_shortcuts = [identifier for identifier in self._shortcuts if identifier in NODE_ENTRY_BY_ID]
        shortcut_rows = 1 if active_shortcuts and not has_query else 0

        if self._panel_x is None:
            self._panel_x = self._anchor_x - padding - search_width * 0.75
        if self._search_y is None:
            self._search_y = self._anchor_y - search_height / 2

        x = min(max(0, self._panel_x), region.width - width)
        preferred_rows_below = min(4, MAX_RESULTS)
        min_search_y = padding + gap + preferred_rows_below * row_height
        search_y = min(max(min_search_y, self._search_y), region.height - padding - search_height)
        max_rows_below = max(1, int((search_y - gap - padding) // row_height))
        visible_limit = min(MAX_RESULTS, max_rows_below)
        self._visible_limit = visible_limit
        rows = min(visible_limit, max(0, len(self._results) - self._scroll_offset)) if has_query else 0
        empty_rows = 1 if has_query and not self._results else 0
        shortcuts_height = shortcut_rows * (shortcut_gap + shortcut_height)
        height = padding * 2 + search_height + shortcuts_height + (gap + max(rows, empty_rows) * row_height if has_query else 0) + (_scaled(12, scale) if has_query and len(self._results) > rows else 0)
        y = search_y + search_height + padding - height
        self._panel_rect = (x, y, width, height)
        self._padding = padding
        self._search_height = search_height
        self._row_height = row_height

        _draw_rounded_panel(x, y, width, height, radius, PANEL_BACKGROUND)
        _draw_rounded_panel(x + padding, search_y, search_width, search_height, max(4, radius - 1), FIELD_BACKGROUND, BORDER_COLOR)

        query_text = self._query if self._query else "Search nodes..."
        query_color = TEXT_COLOR if self._query else MUTED_TEXT_COLOR
        query_size = _scaled(14, scale)
        search_text_y = search_y + (search_height - _scaled(14, scale)) / 2 + _scaled(2, scale)
        _draw_text("⌕", x + padding + _scaled(12, scale), search_text_y - _scaled(1, scale), _scaled(17, scale), MUTED_TEXT_COLOR)
        query_x = x + padding + _scaled(34, scale)
        _draw_text(query_text, query_x, search_text_y, query_size, query_color)
        if self._query:
            cursor_x = query_x + _text_width(self._query, query_size) + _scaled(2, scale)
            _draw_rect(cursor_x, search_y + _scaled(7, scale), max(1, _scaled(1, scale)), search_height - _scaled(14, scale), TEXT_COLOR)

        self._shortcut_rects = []
        shortcuts_y = search_y - shortcut_gap - shortcut_height
        if active_shortcuts and not has_query:
            item_gap = _scaled(5, scale)
            item_width = (search_width - item_gap * (min(len(active_shortcuts), 10) - 1)) / min(len(active_shortcuts), 10)
            for index, identifier in enumerate(active_shortcuts[:10]):
                item_x = x + padding + index * (item_width + item_gap)
                rect = (item_x, shortcuts_y, item_width, shortcut_height)
                self._shortcut_rects.append((identifier, rect))
                _draw_rounded_panel(item_x, shortcuts_y, item_width, shortcut_height, max(3, radius - 1), FIELD_BACKGROUND, BORDER_COLOR)
                entry = NODE_ENTRY_BY_ID[identifier]
                shortcut_text_size = _scaled(11, scale)
                shortcut_text = _fit_text(_abbreviate_label(entry.label), item_width - _scaled(14, scale), shortcut_text_size)
                _draw_text(shortcut_text, item_x + _scaled(7, scale), shortcuts_y + _scaled(8, scale), shortcut_text_size, TEXT_COLOR)

        rows_top = search_y - shortcuts_height - gap
        self._rows_top = rows_top
        if not has_query:
            return

        if not self._results:
            _draw_text("No results found", x + padding + _scaled(8, scale), rows_top - _scaled(20, scale), _scaled(13, scale), TEXT_COLOR)
            return

        visible_results = self._results[self._scroll_offset:self._scroll_offset + visible_limit]
        for visible_index, entry in enumerate(visible_results):
            index = self._scroll_offset + visible_index
            row_y = rows_top - (visible_index + 1) * row_height
            is_selected = index == self._selected_index
            is_favorite = entry.identifier in self._favorites
            if is_selected:
                _draw_rounded_panel(x + padding, row_y + _scaled(2, scale), search_width, row_height - _scaled(4, scale), max(3, radius - 2), HIGHLIGHT_COLOR, HIGHLIGHT_BORDER_COLOR)

            row_text_y = row_y + _scaled(7, scale)
            category_x = x + padding + _scaled(10, scale)
            category_text = f"{entry.category} >"
            blf.size(FONT_ID, _scaled(12, scale))
            category_width = blf.dimensions(FONT_ID, category_text)[0]
            label_x = category_x + category_width + _scaled(8, scale)
            _draw_text(category_text, category_x, row_text_y, _scaled(11, scale), MUTED_TEXT_COLOR)
            _draw_text(entry.label, label_x, row_text_y, _scaled(13, scale), TEXT_COLOR)
            if is_favorite:
                fav_width = _scaled(10, scale)
                fav_height = _scaled(18, scale)
                fav_x = x + width - padding - fav_width - _scaled(8, scale)
                fav_y = row_y + (row_height - fav_height) / 2
                _draw_rounded_rect(fav_x, fav_y, fav_width, fav_height, _scaled(3, scale), (0.45, 0.45, 0.46, 0.95))

        if has_query and len(self._results) > self._scroll_offset + rows:
            _draw_text("▼", x + width / 2 - _scaled(4, scale), y + _scaled(4, scale), _scaled(12, scale), TEXT_COLOR)

        if self._context_menu_index is not None:
            menu_x, menu_y, menu_width, menu_height = self._context_menu_rect
            menu_row_height = menu_height / 4
            _draw_rounded_panel(menu_x, menu_y, menu_width, menu_height, radius, PANEL_BACKGROUND)
            labels = (("FAVORITE", "Add Favorite"), ("UNFAVORITE", "Remove Favorite"), ("SHORTCUT", "Add Shortcut"), ("UNSHORTCUT", "Remove Shortcut"))
            for index, (action, label) in enumerate(labels):
                row_y = menu_y + menu_height - (index + 1) * menu_row_height
                if self._context_menu_hover == action:
                    _draw_rounded_panel(menu_x + 4, row_y + 3, menu_width - 8, menu_row_height - 6, max(3, radius - 2), HIGHLIGHT_COLOR, HIGHLIGHT_BORDER_COLOR)
                _draw_text(label, menu_x + _scaled(12, scale), row_y + _scaled(8, scale), _scaled(13, scale), TEXT_COLOR)

        if self._shortcut_hover and self._shortcut_hover in NODE_ENTRY_BY_ID:
            entry = NODE_ENTRY_BY_ID[self._shortcut_hover]
            tooltip_text = entry.label
            tooltip_width = _text_width(tooltip_text, _scaled(12, scale)) + _scaled(18, scale)
            tooltip_height = _scaled(24, scale)
            tooltip_x = min(max(x + padding, self._anchor_x), x + width - tooltip_width - padding)
            tooltip_y = shortcuts_y - tooltip_height - _scaled(4, scale)
            if tooltip_y < y + padding:
                tooltip_y = shortcuts_y + shortcut_height + _scaled(4, scale)
            _draw_rounded_panel(tooltip_x, tooltip_y, tooltip_width, tooltip_height, max(3, radius - 1), FIELD_BACKGROUND, BORDER_COLOR)
            _draw_text(tooltip_text, tooltip_x + _scaled(9, scale), tooltip_y + _scaled(7, scale), _scaled(12, scale), TEXT_COLOR)


class NODECONSOLE_OT_RemoveFavorite(Operator):
    bl_idname = "node_console.remove_favorite"
    bl_label = "Remove Favorite"
    bl_description = "Remove this node from Node Console favorites"
    bl_options = {"INTERNAL"}

    identifier: StringProperty()

    def execute(self, _context):
        _remove_favorite(self.identifier)
        return {"FINISHED"}


class NODECONSOLE_OT_RemoveShortcut(Operator):
    bl_idname = "node_console.remove_shortcut"
    bl_label = "Remove Shortcut"
    bl_description = "Remove this node shortcut"
    bl_options = {"INTERNAL"}

    identifier: StringProperty()

    def execute(self, _context):
        _remove_shortcut(self.identifier)
        return {"FINISHED"}


class NODECONSOLE_OT_MoveShortcut(Operator):
    bl_idname = "node_console.move_shortcut"
    bl_label = "Move Shortcut"
    bl_description = "Move this shortcut"
    bl_options = {"INTERNAL"}

    identifier: StringProperty()
    direction: StringProperty(default="UP")

    def execute(self, _context):
        _move_shortcut(self.identifier, -1 if self.direction == "UP" else 1)
        return {"FINISHED"}


class ENS_AddonPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    display_mode: EnumProperty(
        name="Search Result Display",
        description="How node names are shown in the custom search panel",
        items=(
            ("ENGLISH", "English", "Show only English names"),
            ("CHINESE", "Chinese", "Show only translated names where available"),
            ("ENGLISH_CHINESE", "English / Chinese", "Show English names first with Chinese translations"),
            ("CHINESE_ENGLISH", "Chinese / English", "Show Chinese translations first with English names"),
        ),
        default="ENGLISH_CHINESE",
        update=_preference_changed,
    )
    shortcut_key: EnumProperty(
        name="Shortcut Key",
        description="Keyboard key used to open Node Console in the node editor",
        items=(
            ("A", "A", ""),
            ("SPACE", "Space", ""),
            ("F", "F", ""),
            ("S", "S", ""),
            ("TAB", "Tab", ""),
        ),
        default="A",
        update=_shortcut_changed,
    )
    shortcut_shift: BoolProperty(
        name="Shift",
        description="Require Shift for the Node Console shortcut",
        default=True,
        update=_shortcut_changed,
    )
    shortcut_ctrl: BoolProperty(
        name="Ctrl",
        description="Require Ctrl for the Node Console shortcut",
        default=False,
        update=_shortcut_changed,
    )
    shortcut_alt: BoolProperty(
        name="Alt",
        description="Require Alt for the Node Console shortcut",
        default=False,
        update=_shortcut_changed,
    )
    ui_scale: FloatProperty(
        name="Console Size",
        description="Adjust the Node Console text and panel size",
        default=1.0,
        min=1.0,
        max=2.0,
        soft_min=1.0,
        soft_max=2.0,
        step=10,
        update=_preference_changed,
    )
    favorites_json: StringProperty(
        name="Favorite Nodes",
        description="Internal favorite node storage",
        default="[]",
        options={"HIDDEN"},
    )
    favorite_meta_json: StringProperty(
        name="Favorite Node Names",
        description="Internal favorite node display names",
        default="{}",
        options={"HIDDEN"},
    )

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, "display_mode")
        layout.prop(self, "ui_scale")

        box = layout.box()
        box.label(text="Shortcut")
        row = box.row(align=True)
        row.prop(self, "shortcut_key", text="")
        row.prop(self, "shortcut_shift", toggle=True)
        row.prop(self, "shortcut_ctrl", toggle=True)
        row.prop(self, "shortcut_alt", toggle=True)

        favorites = _load_favorites()
        favorite_meta = _load_favorite_meta()
        box = layout.box()
        box.label(text="Favorites")
        if not favorites:
            box.label(text="No favorite nodes")
            return

        for identifier in sorted(favorites, key=lambda item: favorite_meta.get(item, item).lower()):
            row = box.row(align=True)
            row.label(text=favorite_meta.get(identifier, identifier))
            remove_op = row.operator(NODECONSOLE_OT_RemoveFavorite.bl_idname, text="", icon="X")
            remove_op.identifier = identifier

        shortcuts = _load_shortcuts()
        box = layout.box()
        box.label(text="Shortcuts")
        if not shortcuts:
            box.label(text="No node shortcuts")
            return

        for identifier in shortcuts:
            entry = NODE_ENTRY_BY_ID.get(identifier)
            row = box.row(align=True)
            row.label(text=entry.label if entry else favorite_meta.get(identifier, identifier))
            up_op = row.operator(NODECONSOLE_OT_MoveShortcut.bl_idname, text="", icon="TRIA_UP")
            up_op.identifier = identifier
            up_op.direction = "UP"
            down_op = row.operator(NODECONSOLE_OT_MoveShortcut.bl_idname, text="", icon="TRIA_DOWN")
            down_op.identifier = identifier
            down_op.direction = "DOWN"
            remove_op = row.operator(NODECONSOLE_OT_RemoveShortcut.bl_idname, text="", icon="X")
            remove_op.identifier = identifier


classes = (
    ENS_AddNodeByEnglishSearch,
    NODECONSOLE_OT_RemoveFavorite,
    NODECONSOLE_OT_RemoveShortcut,
    NODECONSOLE_OT_MoveShortcut,
    ENS_AddonPreferences,
)


def refresh_keymap():
    unregister_keymap()
    register_keymap()


def register_keymap():
    prefs = _preferences()

    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if not keyconfig:
        return

    keymap = keyconfig.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
    key_type = prefs.shortcut_key if prefs else "A"
    shift = prefs.shortcut_shift if prefs else True
    ctrl = prefs.shortcut_ctrl if prefs else False
    alt = prefs.shortcut_alt if prefs else False
    keymap_item = keymap.keymap_items.new(
        ENS_AddNodeByEnglishSearch.bl_idname,
        type=key_type,
        value="PRESS",
        shift=shift,
        ctrl=ctrl,
        alt=alt,
    )
    KEYMAP_ITEMS.append((keymap, keymap_item))


def unregister_keymap():
    while KEYMAP_ITEMS:
        keymap, keymap_item = KEYMAP_ITEMS.pop()
        try:
            keymap.keymap_items.remove(keymap_item)
        except Exception:
            pass


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    _load_preferences_from_settings()
    register_keymap()


def unregister():
    unregister_keymap()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
