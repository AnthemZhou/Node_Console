# Node Console

<img width="1920" height="600" alt="节点控制台 02" src="https://github.com/user-attachments/assets/c0468802-5677-4372-92f9-28a31d0f6dd7" />


![Blender](https://img.shields.io/badge/Blender-5.1.2%20%7C%205.2.2%20LTS-f5792a?logo=blender&logoColor=white)
![Version](https://img.shields.io/badge/version-1.2.1-blue)
![Category](https://img.shields.io/badge/category-Node%20Editor-555)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

作者：Anthem  
版本：1.2.1

## 中文

Node Console 是一个 Blender 节点搜索插件。它会替换节点编辑器里的 `Shift + A` 搜索，让你可以用英文或拼音搜索节点，并通过 favorite 和 shortcut 自定义搜索权重。拼音搜索可以减少在 Blender 中切换输入法带来的操作卡顿感。界面保持紧凑，视觉风格接近 Blender 原生搜索。

### 功能

- 支持英文和拼音搜索，并提供中英双语结果显示，不依赖当前 Blender 界面语言。
- 支持收藏节点和快捷节点。favorite 和 shortcut 可以自定义搜索权重，也方便快速创建常用节点。
- 在搜索结果左侧显示节点类型颜色标签，方便根据节点类型快速检索。
- 支持手动刷新节点库，可以检索并分类 Asset Library 和外部导入的节点组。
- 支持将一组节点及其连接保存为可复用的「组合点」，并通过英文或拼音快速检索。

### 拼音搜索

Node Console 将拼音搜索作为主要中文检索方式。你可以直接输入 `shili`、`suiji`、`zhuoseqi` 这类拼音来搜索中文节点名，不需要在建模过程中频繁切换输入法，也不需要先把拼音转换成中文。这样可以减少输入法切换带来的停顿感，让 `Shift + A` 搜索保持更连贯的操作节奏。

### 安装

1. 选择 `Node_Console_1.2.1.zip` 安装包。
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

### 组合点

1. 在节点编辑器中选中需要复用的节点或 Frame。
2. 按 `Ctrl + Shift + G`；macOS 默认按 `Command + Shift + G`。
3. 输入组合点名称并选择类目。名称用于后续英文或拼音检索；没有 Frame 时，插件会自动创建 Frame。
4. 按 `Shift + A` 打开 Node Console，然后按键盘 Tab 上方的反引号键 `` ` `` 进入「组合点」模式。中文输入法产生的 `·` 同样有效。
5. 输入组合点名称或拼音，按 Enter 或点击结果，将整组节点及其内部连接放回当前节点编辑器。
6. 再按一次 `` ` `` / `·` 可返回普通节点搜索；切换模式时会保留当前输入内容。
7. 右键组合点结果，可以添加或取消收藏，也可以删除该组合点。

组合点保存在外部 JSON 库文件中。你可以在偏好设置中调整保存组合点的快捷键、查看组合点库路径，并展开组合点列表进行管理。

### 偏好设置

- `搜索结果显示`（Search Result Display）：选择 English、中文、English / 中文 或 中文 / English。
- `搜索窗口大小`（Console Size）：调整搜索窗口整体尺寸，范围是 0.5 到 2.0。
- `搜索窗口宽度`（Console Width）：调整搜索窗口横向宽度，默认是 400，也可以在搜索框右侧拖拽后同步保存。
- `显示缓存的资产节点`（Show Cached Asset Nodes）：在搜索结果中显示已缓存的资产节点组。
- `类目颜色显示`（Category Color Display）：选择类目颜色底块、左侧颜色竖线或关闭类目颜色装饰。
- `刷新资产索引`（Refresh Asset Index）：手动刷新资产节点缓存。
- `快捷键`（Shortcut）：修改打开 Node Console 的快捷键。
- `保存组合点快捷键`（Save Snippet Node Shortcut）：修改保存当前选中节点组合的快捷键。
- `组合点库`（Snippet Libraries）：查看组合点 JSON 库文件的位置和已保存的组合点。
- `收藏`（Favorites）：查看并删除收藏节点。
- `快捷节点`（Shortcuts）：查看、删除或调整快捷节点顺序。

### 说明

- Node Console 以普通 Blender 插件 zip 格式发布。
- 插件不会修改 Blender 的语言文件、节点标签或接口标签。
- 1.2.1 修正着色器、脚本、部分几何与输出节点及 Split Toning 资产的颜色标签；Shader 类组合点也使用专用着色器绿色。节点仍按当前版本的真实注册类型与创建能力生成索引，不会在旧版中展示不存在的新节点。
- 中文名优先读取当前 Blender 的官方简中词典及翻译上下文，不切换你的界面语言；人工搜索别名单独记录。英文、中文、全拼和完整首字母均可检索，例如 `Mesh Bevel`、`网格倒角`、`wanggedaojiao`、`wgdj`。
- 升级 Blender 后，可用「刷新资产索引」发现新版自带的资产节点组。只索引本地可读取的 `.blend` 资产，不会把未下载的在线资产当作可直接添加的节点。
- [变更日志](CHANGELOG.md)与[1.2.1 实测明细](VALIDATION_1.2.1.md)记录了配色修正与回归范围；节点覆盖和译名来源见 [1.2.0 验证报告](VALIDATION_1.2.0.md)。

## English

Node Console is a custom node search add-on for Blender. It replaces the default `Shift + A` search in the Node Editor. You can search nodes by English name or pinyin, and use favorites and shortcuts to customize search weighting. Pinyin search helps avoid the small interaction stutter that can happen when switching input methods inside Blender. The layout stays compact and is inspired by Blender native search.

### Features

- Supports English and pinyin search with bilingual result display, independent of the current Blender interface language.
- Supports favorite nodes and shortcut nodes. Favorites and shortcuts can customize search weighting and make common nodes faster to create.
- Shows colored node type tags on the left side of search results, making nodes easier to scan by type.
- Supports manual node library refresh, including searchable and categorized Asset Library or externally imported node groups.
- Saves connected node sets as reusable Snippet Nodes that can be found by English or pinyin.

### Pinyin Search

Node Console treats pinyin as the primary way to search Chinese node names. You can type pinyin such as `shili`, `suiji`, or `zhuoseqi` directly, without switching input methods or converting it into Chinese characters first. This keeps `Shift + A` search responsive and avoids the small interruptions that can come from input-method switching during node work.

### Install

1. Choose the `Node_Console_1.2.1.zip` installation package.
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

### Snippet Nodes

1. Select the nodes or frame you want to reuse in a node editor.
2. Press `Ctrl + Shift + G`; on macOS, the default is `Command + Shift + G`.
3. Enter a required snippet name and choose a category. If the selection has no frame, Node Console creates one automatically.
4. Press `Shift + A` to open Node Console, then press the backtick key `` ` `` above Tab to enter Snippet Node mode. The `·` character produced by a Chinese input method is also supported.
5. Search by the snippet name or its pinyin, then press Enter or click the result to insert the complete node set with its internal links.
6. Press `` ` `` or `·` again to return to regular node search. The current query is preserved while switching modes.
7. Right-click a snippet result to add or remove its favorite status, or to delete the snippet.

Snippet Nodes are stored in an external JSON library file. Preferences provide controls for the save shortcut, the library path, and the expandable list of saved snippets.

### Preferences

- `Search Result Display`: choose English, 中文, English / 中文, or 中文 / English.
- `Console Size`: adjusts the search panel size from 0.5 to 2.0.
- `Console Width`: adjusts the horizontal search panel width, defaults to 400, and stays in sync with right-edge dragging in the search panel.
- `Show Cached Asset Nodes`: shows cached Asset Library node groups in search results.
- `Category Color Display`: chooses colored category blocks, left-side color lines, or no category color decoration.
- `Refresh Asset Index`: rebuilds the asset node cache manually.
- `Shortcut`: changes the key and modifiers used to open Node Console.
- `Save Snippet Node Shortcut`: changes the shortcut used to save the selected node set.
- `Snippet Libraries`: shows the snippet JSON library location and saved snippets.
- `Favorites`: lists favorite nodes and lets you remove them.
- `Shortcuts`: lists shortcut nodes and lets you remove or reorder them.

### Notes

- Node Console is released as a regular Blender add-on zip.
- The add-on does not modify Blender language files, node labels, or socket labels.
- Version 1.2.1 corrects shader, script, selected geometry/output and Split Toning asset colors. Shader snippets now use dedicated shader green. Runtime registration and native creation checks still determine which nodes are offered in each editor.
- Chinese labels use the running Blender's official Simplified Chinese catalog and translation contexts without changing the UI language. Editorial search aliases are stored separately. Search supports English, Chinese, full pinyin and complete initials, such as `Mesh Bevel`, `网格倒角`, `wanggedaojiao` and `wgdj`.
- After upgrading Blender, use Refresh Asset Index to discover new bundled node groups. Only locally readable `.blend` assets are indexed; undownloaded online assets are not presented as directly creatable nodes.
- See the [changelog](CHANGELOG.md) and [1.2.1 validation details](VALIDATION_1.2.1.md) for color fixes and testing limits. Node coverage and translation sources remain documented in the [1.2.0 report](VALIDATION_1.2.0.md).
