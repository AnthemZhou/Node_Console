# Node Console

![Blender](https://img.shields.io/badge/Blender-5.1.2-f5792a?logo=blender&logoColor=white)
![Version](https://img.shields.io/badge/version-0.8.32-blue)
![Category](https://img.shields.io/badge/category-Node%20Editor-555)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

Author: Anthem  
Version: 0.8.32

## English

Node Console is a custom Blender node search console for the Node Editor. It replaces the default `Shift + A` search with a language-independent launcher that can search English names, Chinese names, and pinyin while keeping a compact visual layout inspired by Blender native search.

### Features

- Replaces `Shift + A` in the Node Editor with a custom node console.
- Searches Blender built-in shader, geometry, compositor, and texture nodes independent of the current UI language.
- Supports English, Chinese, bilingual display, and pinyin search.
- Uses macOS system pinyin conversion when available, with a bundled fallback table for Windows and Linux.
- Offers optional Chinese fuzzy matching for sparse queries such as `设置法向` matching `设置曲线法向`.
- Shows colored category tags to hint at node type while keeping the node name readable.
- Supports favorites and search shortcuts.
- Shows shortcuts under the search field and allows quick creation from them.
- Supports cached Asset Library node groups via manual refresh.
- Keeps the newly created node selected and lets it follow the mouse before placement.
- Saves preferences, favorites, shortcuts, and asset cache outside Blender add-on preference storage.

### Install

1. Download `Node_Console_0.8.32.zip` from the release assets.
2. In Blender, open `Edit > Preferences > Add-ons`.
3. Click `Install...` and choose the zip file.
4. Enable `Node Console`.

### Usage

1. Open any node editor.
2. Press `Shift + A`.
3. Type an English name, Chinese name, or pinyin, such as `instance`, `实例`, `shili`, `noise`, or `zaobo`.
4. Press Enter or click a result to create the node.
5. Move the mouse to position the node, then click or press Enter to place it.
6. Right-click a result to add or remove favorites and shortcuts.

### Preferences

- `Search Result Display`: choose English, Chinese, English / Chinese, or Chinese / English.
- `Enable Chinese Fuzzy Match`: enables sparse Chinese/pinyin matching. This is off by default because it may slightly slow live search.
- `Console Size`: adjusts the console text and panel size.
- `Show Cached Asset Nodes`: includes cached Asset Library node groups in search results.
- `Refresh Asset Index`: rebuilds the asset node cache.
- `Shortcut`: changes the key and modifiers used to open Node Console.
- `Favorites`: lists favorite nodes and lets you remove them manually.
- `Shortcuts`: lists shortcut nodes and lets you remove or reorder them manually.

## 中文

Node Console 是一个用于 Blender 节点编辑器的自定义节点搜索插件。它会替换默认的 `Shift + A` 搜索，让你在不同界面语言下都可以用英文、中文或拼音搜索节点，同时保留接近 Blender 原生搜索的紧凑视觉体验。

### 功能

- 用自定义节点搜索窗口替换节点编辑器中的 `Shift + A`。
- 不依赖当前 Blender 界面语言，搜索内置 Shader、Geometry、Compositor、Texture 节点。
- 支持英文、中文、中英双语显示，以及拼音搜索。
- macOS 上优先使用系统拼音转换，Windows 和 Linux 使用插件内置的拼音兜底表。
- 可选开启中文模糊检索，例如用 `设置法向` 匹配 `设置曲线法向`。
- 在搜索结果左侧显示节点类型颜色标签，方便快速辨认节点类型。
- 支持收藏节点和快捷节点。
- 在搜索框下方显示快捷节点，可以直接点击生成。
- 支持手动刷新并搜索 Asset Library 中缓存的节点组资产。
- 新建节点后保持选中，并跟随鼠标移动，点击后落位。
- 将显示模式、收藏、快捷节点和资产缓存保存到独立设置文件中。

### 安装

1. 从 release assets 下载 `Node_Console_0.8.32.zip`。
2. 在 Blender 中打开 `编辑 > 偏好设置 > 插件`。
3. 点击 `安装...` 并选择这个 zip 文件。
4. 启用 `Node Console`。

### 使用

1. 打开任意节点编辑器。
2. 按 `Shift + A`。
3. 输入英文、中文或拼音，例如 `instance`、`实例`、`shili`、`noise`、`zaobo`。
4. 按 Enter 或点击搜索结果来创建节点。
5. 移动鼠标决定节点位置，再点击或按 Enter 落位。
6. 右键搜索结果，可以添加或取消收藏，也可以添加快捷节点。

### 偏好设置

- `Search Result Display`：选择 English、中文、English / 中文、中文 / English。
- `Enable Chinese Fuzzy Match`：开启中文跳词模糊检索。默认关闭，因为它可能让实时搜索略微变慢。
- `Console Size`：调整搜索窗口整体尺寸。
- `Show Cached Asset Nodes`：在搜索结果中显示已缓存的资产节点组。
- `Refresh Asset Index`：手动刷新资产节点缓存。
- `Shortcut`：修改打开 Node Console 的快捷键。
- `Favorites`：查看并删除收藏节点。
- `Shortcuts`：查看、删除或调整快捷节点顺序。

## Notes

- Node Console is released as a regular Blender add-on zip.
- A `blender_manifest.toml` draft is kept in the repository for possible future Blender Extensions packaging.
- The add-on does not modify Blender language files, node labels, or socket labels.
