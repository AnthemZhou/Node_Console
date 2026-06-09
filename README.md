# Node Console

![Blender](https://img.shields.io/badge/Blender-4.0%2B-f5792a?logo=blender&logoColor=white)
![Version](https://img.shields.io/badge/version-0.7.28-blue)
![Category](https://img.shields.io/badge/category-Node%20Editor-555)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)

Author: Anthem  
Version: 0.7.28

Node Console is a language-independent Blender node launcher. It replaces the default `Shift + A` node search with a custom console that can search and display node names in English, Chinese, or bilingual formats.

## What It Does

- Replaces `Shift + A` in the Node Editor with a custom node console.
- Searches Blender's built-in shader, geometry, compositor, and texture nodes by English or Chinese name.
- Searches node names and Blender menu-provided node variants without relying on the current UI language.
- Searches cached node group assets from Blender Asset Libraries after you rebuild the cache manually from preferences.
- Restricts text matching to node names and variants, while categories are used only for display.
- Lets you choose result display mode: English, Chinese, English / Chinese, or Chinese / English.
- Shows node categories on the left side of search results, directly followed by the node name like Blender's native search layout.
- Opens near the mouse position, keeps the search field fixed while results expand below it, and uses a Blender-native style panel with subtle borders, rounded corners, and rounded highlights.
- Opens as a search-only box first, then shows results after you type.
- Adds the selected node at the mouse/cursor position.
- Keeps the newly added node selected and lets it follow the mouse until you click to place it.
- Lets you right-click a result and choose `Add Favorite` or `Remove Favorite`.
- Lets you right-click a result and choose `Add Shortcut` or `Remove Shortcut`.
- Shows node shortcuts below the search field, follows the selected display language, shows full names on hover, and supports two-click shortcut removal from the search panel.
- Supports scrolling through long result lists, with a bottom indicator when more results are available.
- Shows favorite nodes in add-on preferences, where they can be removed manually.
- Boosts favorite nodes when they match a future search.
- Saves favorites, display mode, console size, asset index, and shortcut settings outside Blender's add-on preference storage.
- Lets you adjust the console size, shortcut key, favorite nodes, and node shortcuts in add-on preferences.
- Keeps a `blender_manifest.toml` draft in the repository for future Blender Extensions packaging, while release zips remain regular Blender add-ons.
- Does not modify Blender language files, node labels, or socket labels.

## Install

1. Use the generated `Node_Console_0.7.28.zip`.
2. In Blender, open `Edit > Preferences > Add-ons`.
3. Click `Install...` and choose the zip file.
4. Enable `Node Console`.

## Usage

1. Open a node editor.
2. Press `Shift + A`.
3. Type a node name in English or Chinese, such as `instance`, `实例`, `noise`, or `噪波`.
4. Press Enter or left-click a result to create the node.
5. Move the mouse to position the new node, then click or press Enter to place it.
6. Right-click a result to choose favorite or shortcut actions.
7. Click a shortcut under the search field to create that node directly.
8. Click outside the console to close it.

## Preferences

- `Search Result Display`: choose English, Chinese, English / Chinese, or Chinese / English.
- `Console Size`: adjusts the console text and panel size.
- `Show Cached Asset Nodes`: includes cached asset node groups in search results. `Refresh Asset Index` rebuilds the cache immediately after adding or changing Asset Library nodes.
- `Shortcut`: sets the key and modifier combination used to open Node Console. The default is `Shift + A`.
- `Favorites`: lists favorite nodes and lets you remove them manually.
- `Shortcuts`: lists shortcut nodes and lets you remove or reorder them manually.
