# Node Console

<img width="1920" height="600" alt="节点控制台 02" src="https://github.com/user-attachments/assets/c0468802-5677-4372-92f9-28a31d0f6dd7" />


![Blender](https://img.shields.io/badge/Blender-5.1.2%20%7C%205.2.2%20LTS-f5792a?logo=blender&logoColor=white)
![Version](https://img.shields.io/badge/version-1.4.1-blue)
![Category](https://img.shields.io/badge/category-Node%20Editor-555)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

作者：Anthem  
版本：1.4.1

## 中文

Node Console 是一个 Blender 节点搜索插件。它会替换节点编辑器里的 `Shift + A` 搜索，让你可以用英文、中文或拼音搜索节点，并通过 favorite 和 shortcut 自定义搜索权重。1.4.0 已加入 macOS 原生中文输入；1.4.1 在同一自绘框中接入 Windows 系统输入法，Windows 部分尚待实机确认。界面保持紧凑，视觉风格接近 Blender 原生搜索。

### 功能

- 支持英文和拼音搜索，并提供中英双语结果显示，不依赖当前 Blender 界面语言。
- macOS 支持在现有搜索框内直接输入中文，使用系统输入法组词、选择候选词和确认上屏。
- 支持收藏节点和快捷节点。favorite 和 shortcut 可以自定义搜索权重，也方便快速创建常用节点。
- 在搜索结果左侧显示节点类型颜色标签，方便根据节点类型快速检索。
- 支持手动刷新节点库，可以检索并分类 Asset Library 和外部导入的节点组。
- 支持将一组节点及其连接保存为可复用的「组合点」，并通过英文或拼音快速检索。
- 偏好设置支持检查版本、选择版本并确认安装；可选加入 Beta 测试，默认只显示稳定版。

### 中文输入与拼音搜索

macOS 用户可以按 `Shift + A` 后，直接用系统中文输入法输入「集合」「噪波」等节点名。组词中的拼音带下划线，候选词由系统输入法提供；确认中文上屏后更新搜索结果。组词时的回车只确认候选词，不会误创建节点；Esc 先取消组词，搜索框仍然保留。中文上屏后，再按回车即可创建并放置节点。

英文和拼音检索仍然保留，例如 `instance`、`shili`、`zaobo`，不必先转换成中文。也支持粘贴中文节点名后检索（macOS：`Command + V`，Windows/Linux：`Ctrl + V`）。

**平台范围：** macOS 原生中文输入实测于 Apple Silicon Mac、Blender 5.2.2 LTS 和系统拼音输入法。安装包同时包含 arm64/x86_64 原生模块，但 Intel Mac、第三方输入法及多显示器候选框位置尚未实机验证。1.4.1 的 Windows 实现直接调用系统 IMM/Win32 接口，不需要安装 Python 模块；代码和模拟事件测试已覆盖，但尚未在 Windows Blender 中验证微软拼音、候选框、焦点与节点放置，暂不视为验证完成。Linux 仍使用原有英文、拼音和中文粘贴方式。组合点命名继续使用 Blender 原生输入框。原生后端初始化失败时保留原有搜索输入方式。Windows 实测方法见 [输入模块说明](ime_input/README.md)。

### 安装

1. 选择 `Node_Console_1.4.1.zip` 安装包。
2. 在 Blender 中打开 `编辑 > 偏好设置 > 插件`。
3. 点击 `安装...`，选择下载的 zip 文件。
4. 启用 `Node Console`。

### 使用

1. 打开任意节点编辑器。
2. 按 `Shift + A`。
3. 输入英文或拼音，例如 `instance`、`shili`、`noise`、`zaobo`；macOS 也可用中文输入法输入节点名。
4. 按 Enter，或点击搜索结果来创建节点。
5. 移动鼠标决定节点位置。
6. 点击鼠标左键，或按 Enter 落位。
7. 右键搜索结果，可以添加或取消收藏，也可以添加快捷节点。

空搜索时的快捷节点使用纵向普通节点行，沿用类目颜色和中英文显示模式。可拖动节点行排序，松开保存；按 Esc、右键或拖到列表外松开可取消。顺序按几何、材质、合成编辑器分别保存。输入文字后仍是正常节点搜索，不先弹出官方添加菜单。

快捷节点行右侧的三条浅色横线表示可拖动；整行均可按住拖动。按下后轻微提亮，拖动行跟随鼠标，相邻行平滑让位，松开后归位。普通搜索结果和组合点结果不显示排序标记。

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

### 在线更新

在 Node Console 偏好设置中点击「检查更新」，读取 [GitHub Releases](https://github.com/AnthemZhou/Node_Console/releases) 中有安装包的版本；这一步不会下载安装包或替换插件。在版本下拉框选择目标，再点击「安装所选版本」，确认后才下载、校验并替换。当前安装版本会标注，不能重复安装同一版本；不会在启动 Blender 时自动联网。

- 「接受 Beta 测试版本」默认关闭。勾选后重新检查，才会列出 GitHub 标记为 Pre-release 的版本；没有已发布的 Beta 时不会虚构选项。勾选或取消本身不会安装、降级或切换版本。
- 选择 Beta 或较旧版本时，确认框会显示风险或回退提示。允许手动从 Beta 回到稳定版，仍先备份再替换。回退到 1.4.0 等旧版本时，更新界面也会恢复为该版本的样式。
- 1.4.1 本身是正式版，Windows 原生输入后端仍待实机验证，这与以后是否接受 Beta 更新是两个独立事项。

- 需要在 Blender 的 `偏好设置 > 系统` 中允许在线访问；不会替你修改该权限。
- 下载在独立进程中执行，不占用搜索界面的主线程。网络失败、损坏的包或不兼容的 Blender 版本会提示错误，不替换插件。
- 替换前保留本地备份；收藏、快捷节点、排序、使用记录和组合点库不清空。成功后的文件夹按钮可打开旧文件备份，备份保留在插件目录旁的 `.node-console-update-*/previous` 中。
- 下载完成后自动热更新，无需重启 Blender。搜索、节点放置或组合点命名尚未结束时会等待，完成后只重载 Node Console，不重置或重新注册 Blender 和其他插件的快捷键。新版启用失败会尝试恢复原版本；若无法自动恢复，界面会提示重启并检查备份。
- Git 源码工程不接受自动替换。首次使用此按钮需要先安装包含此功能的版本。
- 已安装 1.4.0 的用户可通过原来的「更新」按钮升级到 1.4.1；升级后才出现版本选择和 Beta 开关。从 1.3.0 的旧更新器升级仍需首次重启，1.3.1 起支持后续热加载。

### 说明

- Node Console 以普通 Blender 插件 zip 格式发布。
- 插件不会修改 Blender 的语言文件、节点标签或接口标签。
- 1.2.2 优化搜索匹配与索引准备。Blender 5.2.2 实测搜索核心中位耗时降低约 54%–59%，两版 Blender 共 10,935 次查询对照保持原有结果与排序；详见[性能验证](PERFORMANCE.md)。
- 1.2.1 修正着色器、脚本、部分几何与输出节点及 Split Toning 资产的颜色标签；Shader 类组合点也使用专用着色器绿色。节点仍按当前版本的真实注册类型与创建能力生成索引，不会在旧版中展示不存在的新节点。
- 中文名优先读取当前 Blender 的官方简中词典及翻译上下文，不切换你的界面语言；人工搜索别名单独记录。英文、中文、全拼和完整首字母均可检索，例如 `Mesh Bevel`、`网格倒角`、`wanggedaojiao`、`wgdj`。
- 升级 Blender 后，可用「刷新资产索引」发现新版自带的资产节点组。只索引本地可读取的 `.blend` 资产，不会把未下载的在线资产当作可直接添加的节点。
- 节点支持、译名处理与配色修正的版本变化见[变更日志](CHANGELOG.md)。

## English

Node Console is a custom node search add-on for Blender. It replaces the default `Shift + A` search in the Node Editor. Search by English name, Chinese or pinyin, and use favorites and shortcuts to customize search weighting. Version 1.4.0 introduced native macOS Chinese input. Version 1.4.1 adds release selection with optional Beta updates and a Windows system IME backend pending live Windows validation. The layout stays compact and is inspired by Blender native search.

### Features

- Supports English and pinyin search with bilingual result display, independent of the current Blender interface language.
- Supports native Chinese composition, system candidates and committed text in the existing search field on macOS.
- Supports favorite nodes and shortcut nodes. Favorites and shortcuts can customize search weighting and make common nodes faster to create.
- Shows colored node type tags on the left side of search results, making nodes easier to scan by type.
- Supports manual node library refresh, including searchable and categorized Asset Library or externally imported node groups.
- Saves connected node sets as reusable Snippet Nodes that can be found by English or pinyin.
- Check releases, select a version and confirm installation in Preferences; Beta versions are opt-in and disabled by default.

### Chinese Input and Pinyin Search

On macOS, press `Shift + A` and use your system Chinese input method to type node names such as `集合` or `噪波`. Composition text is underlined; the system provides candidates. Committed Chinese updates search results. Enter during composition confirms a candidate without creating a node; Escape cancels composition while keeping search open. After committing Chinese, press Enter again to create and place the node.

English and direct pinyin search, such as `instance`, `shili` and `zaobo`, remain available. Chinese can still be pasted (`Command + V` on macOS, `Ctrl + V` on Windows/Linux).

**Platform scope:** Native macOS Chinese input was tested on Apple Silicon, Blender 5.2.2 LTS and macOS Pinyin. The package includes arm64/x86_64 code, but Intel Macs, third-party IMEs and multi-monitor candidate positioning have not been tested live. The 1.4.1 Windows backend uses system IMM/Win32 APIs without external Python dependencies. Its simulated message tests do not prove real Microsoft Pinyin composition, candidates, focus or node placement; live Windows Blender validation remains required. Linux retains its original input path. Snippet naming still uses Blender's native text field. Failed backend initialization retains standard search input. See the [input module notes](ime_input/README.md) for Windows testing.

### Install

1. Choose the `Node_Console_1.4.1.zip` installation package.
2. In Blender, open `Edit > Preferences > Add-ons`.
3. Click `Install...`, then choose the downloaded zip file.
4. Enable `Node Console`.

### Usage

1. Open any node editor.
2. Press `Shift + A`.
3. Type an English name or pinyin, such as `instance`, `shili`, `noise`, or `zaobo`; macOS users can also use a Chinese IME.
4. Press Enter, or click a result to create the node.
5. Move the mouse to choose the node position.
6. Click the left mouse button, or press Enter to place the node.
7. Right-click a result to add or remove favorites and shortcuts.

An empty query shows shortcuts as regular vertical node rows with the selected category colors and bilingual display mode. Drag a row and release to save its order; Escape, right-click or an outside drop cancels. Geometry, Shader and Compositor editors keep independent orders. Typing still searches nodes directly, without opening the native Add menu first.

Three subtle horizontal lines at the right of each shortcut row indicate dragging; the entire row remains draggable. Pressing gently brightens it, dragging lifts it under the pointer while neighbors slide aside, and releasing settles it into place. Regular search and snippet results do not show reorder grips.

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

### Online Updates

Click Check for Updates in Node Console Preferences to list [GitHub releases](https://github.com/AnthemZhou/Node_Console/releases) with installation packages. Checking only reads metadata. Choose a version, click Install Selected Version, then confirm before anything is downloaded or replaced. The current version is marked and cannot be reinstalled. There are no startup network checks.

- Accept Beta Versions is off by default. Enable it and check again to include published GitHub prereleases. No Beta options are fabricated when none exist; changing the checkbox never installs or downgrades the add-on.
- Beta installation and downgrade dialogs display appropriate warnings. Returning from Beta to a stable release is supported with backup and confirmation. Downgrading to an older version such as 1.4.0 also restores that version's older update interface.
- 1.4.1 is a stable release, but its Windows native IME backend still needs live Windows validation. This limitation is separate from opting into future Beta releases.

- Enable Allow Online Access in Blender Preferences > System. The add-on never changes this permission for you.
- A separate process handles downloads. Network errors, invalid packages and incompatible Blender versions leave the installation untouched.
- A local backup is kept before replacement. Favorites, shortcuts, ordering, usage, settings and snippet libraries are preserved. The folder button after a successful update opens the backup at `.node-console-update-*/previous` beside the installation.
- Updates activate without restarting Blender. Activation waits for node search, placement or snippet naming to finish, then reloads only Node Console. Blender and other add-ons' keymaps are not reset or re-registered. Failed activation attempts to restore the previous version; if recovery fails, a message asks you to restart and check the backup.
- Git source checkouts cannot be replaced through this button. Install a version containing the updater before using this feature for the first time.
- Existing 1.4.0 users can upgrade via the original Update button; version selection appears after installing 1.4.1. Updating from 1.3.0 still requires one restart; 1.3.1 and later support subsequent hot activation.

### Notes

- Node Console is released as a regular Blender add-on zip.
- The add-on does not modify Blender language files, node labels, or socket labels.
- Version 1.2.2 optimizes matching and index preparation. Median core search time is approximately 54%–59% lower on Blender 5.2.2; 10,935 queries across two Blender versions retain identical results and ordering. See [performance results](PERFORMANCE.md).
- Version 1.2.1 corrects shader, script, selected geometry/output and Split Toning asset colors. Shader snippets now use dedicated shader green. Runtime registration and native creation checks still determine which nodes are offered in each editor.
- Chinese labels use the running Blender's official Simplified Chinese catalog and translation contexts without changing the UI language. Editorial search aliases are stored separately. Search supports English, Chinese, full pinyin and complete initials, such as `Mesh Bevel`, `网格倒角`, `wanggedaojiao` and `wgdj`.
- After upgrading Blender, use Refresh Asset Index to discover new bundled node groups. Only locally readable `.blend` assets are indexed; undownloaded online assets are not presented as directly creatable nodes.
- See the [changelog](CHANGELOG.md) for changes to node support, translation handling and category colors.
