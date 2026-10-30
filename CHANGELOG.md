# Changelog

## 1.4.2-beta.1

### 中文

- 搜索框中的「组合点 / Snippet Node」模式标签文字改为与「搜索节点…」占位文字相同的灰度；保留标签底色、输入文字和结果类目颜色。
- 精简更新栏为一行，使用带提示的刷新/安装图标；窄窗口自动分行。
- 版本列表仅保留当前通道最近三个可安装版本。没有更新时默认显示当前版本，即使远端列表暂时缺少当前版本也不会默认降级；旧正式版、Beta、RC 明确区分。
- 本版为 GitHub Pre-release。需在 1.4.1 中勾选「接受 Beta 测试版本」后检查并确认安装；1.4.1 仍是最新正式版。Windows IME 仍待 Windows Blender 实机验证。

### English

- Match the Snippet Node mode badge text to the search placeholder gray, preserving its background, entered text and result category colors.
- Compact the updater into a single row with refresh/install tooltips and a narrow-window fallback. Keep only the three newest eligible releases, never default to a downgrade, and distinguish installed/older stable/Beta/RC versions.
- Publish as a GitHub prerelease, requiring Beta opt-in and confirmation in 1.4.1. Keep 1.4.1 as the latest stable release. Windows IME still needs live Windows Blender validation.

## 1.4.1

### 中文

- 更新器改为「检查版本 → 选择版本 → 确认安装」，检查不下载或替换文件。当前版本标注且不可重复安装；紧凑布局在窄窗口中纵向排列。
- 新增「接受 Beta 测试版本」，默认关闭；支持已发布的 GitHub 预发布版与 Beta/RC 版本排序。允许经确认回退至稳定版，保留本地备份、收藏、权重和组合点库；回退旧版时会同时恢复旧版界面。
- 下载前重新核对所选标签和安装包信息，确认后版本或文件发生变化时停止，不自动改装另一版本。Beta 开关变化不安装或降级，并取消未完成的下载。
- 搜索框内已输入文字和组词文字上移一个缩放像素，保留中文相对英文的基线校正；不移动占位文字、结果行及图标。
- 增加 Windows 系统 IME 后端，在当前 Blender 窗口内接收组词和上屏，保留自绘界面；按原始事件顺序处理文字、退格、回车与组合点模式切换，避免组词按键误触发节点操作。
- 接收器仅在搜索期间存在，关闭、失焦与卸载时释放并恢复原输入上下文；不修改快捷键、输入法语言选择或其他插件配置。
- Windows 目前通过模拟消息和生命周期测试，尚无 Windows Blender 实机输入法验证，不将其等同于正式兼容性确认。macOS 原有后端继续保留，Linux 不变。

### English

- Split updates into checking, version selection and explicit installation confirmation. Checking does not download packages or replace files. Mark the current version and disable reinstalling it; stack controls in narrow layouts.
- Add an off-by-default Beta opt-in, published GitHub prereleases and Beta/RC ordering. Permit confirmed downgrades with local backup and preserved user data; older releases restore their own older update interface.
- Revalidate the selected tag and asset before download. Stop if they changed after confirmation, never silently select another release. Changing Beta opt-in cancels pending downloads without installing or downgrading.
- Raise entered/preedit text by one scaled pixel, retaining relative CJK baseline correction without shifting placeholders, results or icons.
- Add a window-scoped Windows IMM receiver for the existing GPU field. Preserve native event ordering for text, editing, confirmation and Snippet Node mode switching; isolate composition keys from node commands.
- Restore the prior input context on close/focus loss without changing keymaps, keyboard language or other add-on settings. Keep the macOS backend and Linux input path.
- Windows message/lifecycle tests use a fake OS. Real Windows Blender IME validation is still required even though 1.4.1 is published as a stable release.

## 1.4.0

### 中文

- macOS 原生中文输入：在现有自绘搜索框内直接使用系统输入法组词、选择候选词并上屏，无需粘贴或额外输入窗口；原有英文、拼音、中英双语检索继续保留。
- 区分候选确认与节点创建：组词时回车确认候选词，Esc 取消组词；中文上屏后回车创建节点。关闭、重复打开和进入节点放置时正确释放及恢复输入焦点。
- 预编辑拼音显示下划线，候选框跟随输入位置；中文及中英混排文字下移 2 个缩放像素，改善输入框内的纵向对齐。
- 原生模块离线随包提供、校验后加载；加载失败保留原有搜索。输入轮询不再额外提高空闲重绘频率，保留快捷节点拖动与排序交互。沿用原有快捷键注册，不重置其他插件或 Blender 快捷键。
- 原生中文输入实测范围为 Apple Silicon Mac、Blender 5.2.2 LTS、系统拼音输入法。Windows/Linux 暂无原生 IME 支持；Intel Mac 和第三方输入法未实机验证。

### English

- Add native Chinese IME composition, system candidates and committed input inside the existing custom search field on macOS, without pasting or a separate input window. Keep English, pinyin and bilingual search.
- Separate candidate confirmation from node creation: Enter confirms composition, Escape cancels it, and Enter after committing creates the node. Release and restore focus when closing, reopening or placing nodes.
- Underline preedit text and position system candidates at the search caret. Lower Chinese and mixed-text baselines by two scaled pixels for improved vertical alignment.
- Bundle the native receiver offline with integrity validation and standard-input fallback. Keep idle redraws at their original rate while polling input; preserve shortcut drag sorting and existing keymap ownership.
- Native Chinese input was tested on Apple Silicon, Blender 5.2.2 LTS and macOS Pinyin. Windows/Linux do not yet have native IME support; Intel Macs and third-party IMEs have not been tested live.

## 1.3.4

### 中文

- 空搜索的快捷节点行末尾增加三条浅色横线，提示整行可按住拖动；与收藏标签分开预留空间，不在普通搜索或组合点结果上显示。
- 增加按下渐亮、拖动悬浮、相邻行平滑让位和落位动画；保留轻点创建、松开保存排序与取消拖动的规则。高频计时器仅在按住或动画期间运行，不加快边缘滚动。
- 补充中文粘贴、Unicode 字符、退格及中英文/拼音检索回归，明确自绘搜索框尚未完整支持系统中文输入法组词与候选确认；不宣称新增原生 IME 支持。

### English

- Add subtle three-line drag grips to shortcut rows, reserving separate space for favorite tags. Regular search and snippet results do not show reorder grips.
- Ease press feedback, lift the dragged row under the pointer, slide neighboring rows and settle on drop. Preserve click-to-create, release-to-save and cancellation behavior. Run the animation timer only during interaction/settling without accelerating edge scrolling.
- Add regressions for Chinese paste, delivered Unicode, backspace and bilingual/pinyin search. Clarify that the custom field does not implement full native IME composition and candidate confirmation; no new native IME support is claimed.

## 1.3.3

### 中文

- 保留 Shift+A 刚打开、未输入时不高亮条目的行为；输入或粘贴搜索词后，自动高亮第一条匹配结果。
- 编辑搜索词或带搜索词切换组合点模式时，选择回到第一条结果；清空、只有空格或没有匹配结果时不自动高亮。保留鼠标悬停、方向键与回车操作。

### English

- Keep an empty Shift+A popup unhighlighted; automatically select and highlight the first match after typing or pasting a query.
- Reset selection to the first match when editing a query or switching snippet mode with text. Clearing, whitespace-only queries and no matches do not auto-highlight; mouse, arrow-key and Enter controls remain available.

## 1.3.2

### 中文

- 缓存未变化的设置文件，按需读取收藏、快捷节点与当前编辑器索引，避免反复解析整份节点缓存；保留原有文件格式、使用数据和未知设置字段。
- 组合点搜索复用名称、分类和拼音条目，不再每次输入都加载整份节点数据；收藏排序保持实时，外部修改、切换库及显示模式变化后自动刷新。
- 收起组合点列表时跳过隐藏内容的加载；展开时使用轻量摘要，创建组合点时再读取对应的完整节点数据，并检查该组合点是否已被外部删除。
- 设置和组合点库改为同目录临时文件写入后原子替换，拒绝覆盖无法解析的原文件；组合点保存或删除失败时明确报错，失败或重复保存不再遗留新 Frame 或改动原 Frame 名称。
- 修复组合点库版本字段异常时的转换错误，补充数据缓存、保存失败、外部编辑、快捷键交互及热更新回归。实测范围与性能数据见 [性能验证](PERFORMANCE.md)。

### English

- Cache unchanged settings files and copy only requested favorites, shortcuts and editor indexes, preserving the file format, usage data and unknown settings.
- Reuse snippet names, categories and pinyin entries across keystrokes without loading every graph payload. Favorites stay live; external edits, library switches and display changes invalidate the cache.
- Skip hidden snippet-list work; use lightweight summaries when expanded. Read the selected graph on insertion and reject results deleted externally since the search.
- Atomically replace settings and snippet libraries through same-directory temporary files, refusing to overwrite unreadable originals. Report failed snippet saves/deletions and restore frames after failed or duplicate saves.
- Tolerate malformed snippet schema-version values and add persistence, cache, external-edit, interaction and hot-reload regression coverage. See [performance results](PERFORMANCE.md) for measured scope and limitations.

## 1.3.1

### 中文

- 在线更新完成后自动热重载 Node Console，无需退出 Blender；等待当前节点操作结束，保留设置与组合点，启用失败时尝试恢复旧版。
- 完善注销时的计时器与绘制回调清理，避免重载后残留旧回调；不重载其他插件或重置其快捷键。
- 热重载后同步刷新插件列表中的版本信息，确保偏好设置仍可正常显示和访问。
- 更新区改为紧凑的版本号、灰度状态与更新按钮单行布局；窄窗口和较长错误提示自动换行。
- 搜索栏打开时不再默认高亮首项，悬停后高亮、移开后恢复；保留直接回车确认，首次方向键选择从第一项开始。

### English

- Activate downloaded updates without restarting Blender, deferring until node operations finish and preserving preferences and snippets. Attempt recovery to the previous version if activation fails.
- Clean up timers and drawing callbacks on unregister so old callbacks cannot survive a reload; other add-ons and their keymaps remain untouched.
- Refresh add-on metadata after activation so Preferences continues to display the add-on and its current version.
- Compact the update header into one row with version, subdued status and a content-sized action; wrap longer messages on narrow layouts.
- Open search without an initially highlighted row. Highlight on hover and clear on leave, preserving quick Enter and starting keyboard selection at the first result.

## 1.3.0

### 中文

- 将空搜索时的快捷节点按钮改为纵向节点行，复用普通搜索结果的类目颜色和中英文显示模式，支持滚动查看完整快捷列表。
- 支持拖动快捷节点行排序，松开鼠标保存；Esc、右键或拖出列表后松开可取消，不会误添加节点。
- 几何、材质、合成节点编辑器分别保存快捷节点顺序，偏好设置中的上下移动与搜索窗口保持同步；保留已有快捷节点、收藏和使用数据。
- 未修改 Shift+A 的入口或 Blender 原生菜单搜索逻辑。
- 偏好设置新增「更新」按钮：主动点击后检查 GitHub 最新正式版，后台下载并校验安装包，保留本地备份后替换插件；重启 Blender 生效，不在运行中重载快捷键。
- 更新遵守 Blender 联网权限，保留收藏、快捷节点顺序、使用记录、设置和组合点库；安装包异常、版本不兼容或源码工程不会被自动替换。

### English

- Show shortcuts as scrollable node rows when the query is empty, using the regular result category colors and bilingual display modes.
- Reorder shortcut rows by dragging; release to save, or cancel with Escape, right-click or an outside drop without creating a node.
- Store ordering separately for each node editor and share it with the Preferences reorder controls, preserving existing shortcuts, favorites and usage data.
- Keep the Shift+A entry point and native Blender menu-search behavior unchanged.
- Add a Preferences Update button to check the latest stable GitHub release on demand, download and validate it in the background, and replace the installation with a local backup. Restart Blender to activate; no live keymap reload.
- Respect Blender's online-access permission and preserve favorites, shortcut order, usage, settings and snippet libraries. Reject invalid/incompatible packages and refuse to overwrite a source checkout.

## 1.2.2

### 中文

- 优化输入检索：复用不可变节点条目的名称、分类和拼音预处理结果；文本缓存有容量上限，收藏与排序仍实时计算。
- 避免未命中时的拼音回退重复匹配；空查询不再遍历索引。
- 索引重建复用本次节点能力检查结果，减少重复读取 Blender 运行信息；保留打开窗口时对本地节点组、资产与设置的更新。
- Blender 5.2.2 实测搜索核心中位耗时降低约 54%–59%，热索引准备耗时降低约 44%–63%；这些数据不代表整体界面帧率。
- 增加与 1.2.1 的完整搜索结果/排序对照、性能基准与缓存生命周期测试。Blender 5.2.2 与 5.1.2 共 10,935 次查询对照零差异；实测范围和数据见 [性能验证](PERFORMANCE.md)。不改变快捷键、收藏、使用数据或持久化格式。

### English

- Reuse immutable entry text/pinyin preprocessing with bounded text caches; evaluate favorites and ranking live.
- Reuse matches during weak-pinyin fallback and skip matching for empty queries.
- Reuse capability data within each index rebuild while retaining live group, asset and preference updates.
- Reduce measured median core search time by approximately 54%–59% and warm index preparation by 44%–63% on Blender 5.2.2; these are not GUI frame-rate measurements.
- Add baseline result/order comparisons, benchmarks and cache lifecycle regressions: 10,935 queries match 1.2.1 exactly across Blender 5.2.2 and 5.1.2. See [performance results](PERFORMANCE.md). Shortcuts, favorites, usage data and persistence formats are unchanged.

## 1.2.1

### 中文

- 修复 24 个 Shader 节点和 Script 节点的颜色回退，增加独立的着色器绿色与脚本青色，并从当前 Blender 实例补齐旧索引中的对应标签。
- 修正 Curve Length、String to Curves 的几何类颜色，以及 Light Output、Line Style Output 的输出类暗红色；修正 String to Curves 的 RNA 标识匹配。
- 补齐 FILTER、MATTE、DISTORT 颜色映射，修复官方 Split Toning 资产组被显示为通用颜色的问题；Shader 类组合点同步使用着色器绿色。
- 保留未激活 Geometry Viewer、组输入/输出和区域节点的特殊配色；不改快捷键、收藏、使用权重、组合点库或用户设置。
- 增加实际 Blender 节点/资产创建、颜色映射、旧版对比和缓存重建回归。版本升级自动使运行索引缓存失效，无需重置偏好设置。
- 实测 Blender 5.2.2 LTS 与 5.1.2，配色、搜索/创建、用户数据保留及 ZIP 安装启停检查均通过。

### English

- Added dedicated shader/script colors and restored their native tags in legacy index entries, fixing 24 shader nodes and Script.
- Corrected Curve Length, String to Curves, Light Output and Line Style Output colors and the String to Curves RNA match.
- Added FILTER, MATTE and DISTORT mappings, fixing the Split Toning asset fallback. Shader snippets now use shader green.
- Preserved neutral Geometry Viewer/interface colors and zone styling, without changing shortcuts or user data.
- Added real Blender color/create regression tests against 1.2.0, including warm-cache checks. The versioned runtime index rebuilds automatically.
- Tested color/search/create regressions, user-data preservation and ZIP install/enable/disable cycles on Blender 5.2.2 LTS and 5.1.2.

## 1.2.0

### 中文

- 补齐 Blender 5.2 节点检索：几何捆包、列表、集合子级、声音采样、点聚集与合并、网格倒角、属性处理、NURBS、字符串等；同时补入注册类型审计发现的整数矢量、标签过滤及嵌套捆包路径等条目。
- 修复跨编辑器节点遗漏：材质节点中的布尔、整数、矢量与场景时间，以及合成器中的摄像机、物体、矩阵、旋转、字符串、字体和警告节点。合成器新增空白图像、字符串转图像。
- 不再按节点类前缀或继承的 Python 基类 poll 推断编辑器支持，改用当前节点树、节点自身限制和原生创建能力检查。缓存命中后仍补全当前版本添加菜单。
- 中文译名读取当前 Blender 官方简中词典，尊重 RNA 翻译上下文，无需更改用户界面语言。人工别名与官方译名单独维护，旧搜索别名继续保留。
- 修复完整拼音首字母不能稳定命中的问题；改善空格、大小写、多音字和包含英文缩写的拼音处理；支持 5.2 的枚举插口搜索变体。
- 搜索缓存按 Blender 版本、构建、索引结构和实验开关失效。保留已有收藏、快捷节点、使用数据及偏好设置，不改快捷键逻辑。
- 修复资产扫描时名称被载入重命名污染，以及同名不同库资产添加时串用的问题。保留本地资产扫描机制，不增加在线资产下载系统。
- 在 macOS arm64 上实测 Blender 5.2.2 LTS、5.1.2 的节点检索、实际创建、双语与拼音搜索及本地资产兼容性；未进行 Windows/Linux 原生运行或全部节点的数值、渲染与交互放置测试。

### English

- Completed runtime discovery for Blender 5.2 geometry, list, string, attribute, NURBS and compositor nodes, including registered types not covered by the initial candidate list.
- Fixed cross-editor omissions in shaders and compositing. Native creation checks replace assumptions based on class prefixes or inherited Python poll methods.
- Read official Simplified Chinese catalogs with RNA contexts without changing the UI language. Keep editorial aliases separate from official names.
- Fixed complete pinyin-initial matching, whitespace handling and selected polyphonic readings. Added support for searchable enum-socket variants.
- Versioned the index by Blender build, schema and experimental settings while preserving user data and existing shortcuts.
- Fixed asset source-name preservation and same-name library isolation. Undownloaded online assets remain outside the local index.
- Tested node discovery, actual creation, bilingual/pinyin search and local assets on Blender 5.2.2 LTS and 5.1.2 on macOS arm64. Native Windows/Linux runs and exhaustive numerical, rendering and interactive-placement tests were not performed.
