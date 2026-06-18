# Node Console

![Blender](https://img.shields.io/badge/Blender-5.1.2-f5792a?logo=blender&logoColor=white)
![Version](https://img.shields.io/badge/version-0.9.6-blue)
![Category](https://img.shields.io/badge/category-Node%20Editor-555)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

作者：Anthem  
版本：0.9.6

## 中文

Node Console 是一个 Blender 节点搜索插件。它会替换节点编辑器里的 `Shift + A` 搜索，让你可以用英文或拼音搜索节点，并通过 favorite 和 shortcut 自定义搜索权重。界面保持紧凑，视觉风格接近 Blender 原生搜索。

### 功能

- 支持英文、拼音和中英双语结果显示，不依赖当前 Blender 界面语言。
- 支持收藏节点和快捷节点。favorite 和 shortcut 可以自定义搜索权重，也方便快速创建常用节点。
- 在搜索结果左侧显示节点类型颜色标签，方便根据节点类型快速检索。
- 支持手动刷新节点库，可以检索并分类 Asset Library 和外部导入的节点组。

### 当前局限性

由于 Blender 当前的 Python modal 事件接口不能把系统输入法候选框直接接入自绘搜索框，Node Console 暂时无法在自绘搜索框中直接使用中文输入法候选框输入中文。改用 Blender 原生输入框虽然可以获得输入法候选框，但会接管键盘和鼠标事件，导致 Node Console 的快捷节点、搜索结果点击和自绘交互出现监听冲突。因此，这个问题需要等待 Blender 官方进一步开放或改进输入模块后，才能彻底解决。当前版本的解决方式是：直接输入拼音，不需要把拼音转换成中文，也可以检索中文节点名。

### 安装

1. 从 release assets 下载 `Node_Console_0.9.6.zip`。
2. 在 Blender 中打开 `编辑 > 偏好设置 > 插件`。
3. 点击 `安装...`，选择下载的 zip 文件。
4. 启用 `Node Console`。

### 使用

1. 打开任意节点编辑器。
2. 按 `Shift + A`。
3. 输入英文或拼音，例如 `instance`、`shili`、`noise`、`zaobo`。
4. 按 Enter，或点击搜索结果来创建节点。
5. 移动鼠标决定节点位置。
6. 点击鼠标左键，或按 Enter 落位。
7. 右键搜索结果，可以添加或取消收藏，也可以添加快捷节点。

### 偏好设置

- `搜索结果显示`（Search Result Display）：选择 English、中文、English / 中文 或 中文 / English。
- `搜索窗口大小`（Console Size）：调整搜索窗口整体尺寸，范围是 0.5 到 2.0。
- `显示缓存的资产节点`（Show Cached Asset Nodes）：在搜索结果中显示已缓存的资产节点组。
- `类目颜色显示`（Category Color Display）：选择类目颜色底块、左侧颜色竖线或关闭类目颜色装饰。
- `刷新资产索引`（Refresh Asset Index）：手动刷新资产节点缓存。
- `快捷键`（Shortcut）：修改打开 Node Console 的快捷键。
- `收藏`（Favorites）：查看并删除收藏节点。
- `快捷节点`（Shortcuts）：查看、删除或调整快捷节点顺序。

### 说明

- Node Console 以普通 Blender 插件 zip 格式发布。
- 仓库中保留了 `blender_manifest.toml` 草稿，方便未来适配 Blender Extensions 格式。
- 插件不会修改 Blender 的语言文件、节点标签或接口标签。

## English

Node Console is a custom node search add-on for Blender. It replaces the default `Shift + A` search in the Node Editor. You can search nodes by English name or pinyin, and use favorites and shortcuts to customize search weighting. The layout stays compact and is inspired by Blender native search.

### Features

- Supports English and pinyin search with bilingual result display, independent of the current Blender interface language.
- Supports favorite nodes and shortcut nodes. Favorites and shortcuts can customize search weighting and make common nodes faster to create.
- Shows colored node type tags on the left side of search results, making nodes easier to scan by type.
- Supports manual node library refresh, including searchable and categorized Asset Library or externally imported node groups.

### Current Limitations

Blender's current Python modal event API does not expose system IME composition candidates to custom-drawn search fields. Because of this, Node Console cannot directly show or use Chinese IME candidate popups inside its custom search box. Using Blender's native text input can enable IME candidates, but it also takes over keyboard and mouse handling, which conflicts with Node Console's clickable shortcuts, search result interactions, and custom event handling. A complete fix will likely require Blender to expose or improve its input API in a future version. The current workaround is to type pinyin directly. You do not need to convert pinyin into Chinese characters to search Chinese node names.

### Install

1. Download `Node_Console_0.9.6.zip` from the release assets.
2. In Blender, open `Edit > Preferences > Add-ons`.
3. Click `Install...`, then choose the downloaded zip file.
4. Enable `Node Console`.

### Usage

1. Open any node editor.
2. Press `Shift + A`.
3. Type an English name or pinyin, such as `instance`, `shili`, `noise`, or `zaobo`.
4. Press Enter, or click a result to create the node.
5. Move the mouse to choose the node position.
6. Click the left mouse button, or press Enter to place the node.
7. Right-click a result to add or remove favorites and shortcuts.

### Preferences

- `Search Result Display`: choose English, 中文, English / 中文, or 中文 / English.
- `Console Size`: adjusts the search panel size from 0.5 to 2.0.
- `Show Cached Asset Nodes`: shows cached Asset Library node groups in search results.
- `Category Color Display`: chooses colored category blocks, left-side color lines, or no category color decoration.
- `Refresh Asset Index`: rebuilds the asset node cache manually.
- `Shortcut`: changes the key and modifiers used to open Node Console.
- `Favorites`: lists favorite nodes and lets you remove them.
- `Shortcuts`: lists shortcut nodes and lets you remove or reorder them.

### Notes

- Node Console is released as a regular Blender add-on zip.
- A `blender_manifest.toml` draft is kept in the repository for possible future Blender Extensions packaging.
- The add-on does not modify Blender language files, node labels, or socket labels.
