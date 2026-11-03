# Changelog

## 1.5.1

<!-- node-console-summary: {"zh":"偏好设置布局整理","en":"Preferences layout cleanup"} -->

### 中文

- 移除需要登录 GitHub 的问题反馈入口及相关文档说明。
- 将「组合点」置于「组合点库」上方；收起组合点列表不影响下方库设置。
- 保留现有多语言搜索、收藏、快捷节点、使用权重和组合点数据。
- 在隔离的 macOS Blender 5.2.2 LTS / 5.1.2 中验证偏好设置布局及安装；未新增 Windows 实机测试。

### English

- Remove the feedback entry requiring GitHub sign-in and its documentation.
- Show Snippet Nodes above Snippet Libraries; keep library settings visible when the list is collapsed.
- Preserve multilingual search, favorites, shortcuts, usage weights and snippet data.
- Validate Preferences layout and installation in isolated macOS Blender 5.2.2 LTS / 5.1.2; no new Windows hardware tests.

## 1.5.0

<!-- node-console-summary: {"zh":"多语言节点搜索","en":"Multilingual node search"} -->

### 中文

- 新增节点语言选择：英文始终可检索，第二语言可选择中文、日语、韩语、俄语或西班牙语；显示模式同步使用所选语言，保留原有中文设置。
- 从当前 Blender 安装包按上下文读取官方节点名、操作变体和菜单路径；缺译回退英文，不修改 Blender 界面语言。中文人工搜索别名与拼音增强继续保留，不将日文汉字转换成中文拼音。
- 新语言支持 Unicode 大小写、全半角及组合字符规范化；仅准备所选语言词典与索引，缓存按语言隔离。保留节点标识、收藏、快捷节点、使用记录、组合点和现有输入操作。
- 补齐日语平/片假名匹配、韩语声母/去空格/未完成音节、俄语 `е/ё` 和西语省重音检索，保留日语浊音、西语 `ñ` 与俄语软硬音符的区别；同样支持用户组合点名称，不改写显示文字。
- 英文和本地语言分别排序，避免双语路径混排改变常用英文顺序；西语按最强匹配选择语言，同分优先英文。匹配规范化与官方原文排序分离。
- 偏好设置底部新增原生问题反馈输入框与灰色占位提示；打开预填 GitHub Issue 草稿，由用户登录并确认后公开提交。不自动发送、上传项目或保存反馈到配置文件。
- README 提供中、英、日、韩、俄、西六种语言说明；中文默认展开，其他语言可按需展开。
- 保留原生评分公式；中文模式与 1.4.7 的完整结果顺序回归及既有原生样本无退步。新语言同时匹配英文和官方译名，不声称与单语言原生菜单完全同序。
- 测试使用隔离的 macOS Blender 5.2.2/5.1.2。新增语言的真实 Mac/Windows 输入法候选窗与键盘布局尚需实机验收，合成事件测试不等同于系统输入法测试。具体范围见 PERFORMANCE.md。

### English

- Add a node-language selector: search English plus Chinese, Japanese, Korean, Russian or Spanish, with matching single/bilingual display options. Preserve existing Chinese preferences.
- Read context-aware node names, operation variants and menu paths from the installed Blender catalogs, falling back to English without changing Blender's UI language. Keep Chinese editorial aliases/pinyin separate from official translations; never transliterate Japanese kanji as Chinese.
- Normalize Unicode case, width and composed characters for new locales. Load only the selected catalog/index, isolate caches by locale and preserve node IDs, favorites, shortcuts, usage, snippets and input interaction.
- Match Japanese kana forms, Korean initial consonants/space-free input/unfinished syllables, Russian `е/ё` and unaccented Spanish, including snippet names. Retain voiced kana, Spanish `ñ` and Russian hard/soft signs; never rewrite display names.
- Rank English and localized paths separately; Spanish chooses the stronger match, favoring English on ties. Preserve official source spelling for native tie ordering and lengths independently of matching normalization.
- Add a native feedback field with a muted placeholder at the bottom of Preferences. Open a prefilled GitHub Issue draft for signed-in users to review and publish; do not send automatically, upload project data or persist feedback in settings.
- Provide Chinese, English, Japanese, Korean, Russian and Spanish README guides, with non-Chinese sections collapsed by default.
- Retain the core native scoring formula and the default Chinese-mode ordering from 1.4.7. New locales match both English and translated paths, so they are not claimed to exactly reproduce a monolingual native menu.
- Validate in isolated macOS Blender 5.2.2/5.1.2 processes. New-locale system IMEs, candidate windows and keyboard layouts still need Mac/Windows hardware acceptance; synthetic input events are not a substitute. See PERFORMANCE.md.

## 1.4.7

<!-- node-console-summary: {"zh":"首次打开与输入提速","en":"Faster opening and search input"} -->

### 中文

- 降低首次打开时的索引准备开销：不再为普通节点生成旧搜索器才使用的整段拼音文本；读取索引时直接转换为独立条目，避免复制整份原始 JSON。
- 原生候选按查询语言准备，并复用已排序的候选列表；保留最近 32 个查询的匹配结果，减少退格、重复输入和取消组词时的重复计算。收藏置顶实时计算，编辑器或条目变化会使结果缓存失效。
- 保持评分公式、结果顺序、组合点检索、快捷键与输入法操作不变；优化不清空收藏、快捷节点、使用记录或设置。
- 本机 Blender 5.2.2 三轮独立进程测试，几何/材质/合成首次无缓存索引准备分别由约 322/172/160 毫秒降至 204/101/104 毫秒。已有缓存读取及未命中查询缓存的搜索也有所改善；核心计算耗时不等于整个弹窗或系统输入法耗时。
- Blender 5.2.2 与 5.1.2 共 23,110 次完整结果顺序对照保持一致，194 组原生样本回归无退步；通过缓存、用户数据及输入绘制回归。本轮未测 Windows/Linux 实机性能，范围与局限见 PERFORMANCE.md。

### English

- Reduce first-open index preparation by skipping obsolete full-text transliteration for native entries and decoding persisted entries without copying the entire raw JSON index.
- Prepare native candidates per query language, reuse their alphabetical order, and retain up to 32 recent query matches for backspace, repeated input and composition cancellation. Apply favorites live and invalidate matches when entries or editor context change.
- Preserve ranking, snippet search, keymaps, IME interaction and user data. Measurements and regression scope are recorded in PERFORMANCE.md.
- Across three isolated Blender 5.2.2 processes, Geometry/Shader/Compositor cold index preparation falls from approximately 322/172/160 to 204/101/104 ms. Persisted-index loading and uncached matching also improve; core timings are not whole-popup or system-IME latency.
- Preserve full result order in 23,110 comparisons across Blender 5.2.2 and 5.1.2, with no regression in the 194 native-search probes. Cache, user-data and input-drawing regressions pass. Windows/Linux hardware performance was not measured in this round; see PERFORMANCE.md for scope and limitations.

## 1.4.6

<!-- node-console-summary: {"zh":"原生搜索结果对齐","en":"Native search result alignment"} -->

### 中文

- 修复官方菜单被其他扩展包装后漏收录“输出”节点的问题；只执行官方菜单回调，不执行第三方追加代码。
- 将旧 RNA 别名正确对应到当前节点，补齐矢量版“映射范围”等官方变体及“类型化捆包”操作。保留已有节点标识，不重置收藏、快捷节点和使用记录。
- 保留资产的原始目录信息，修正搜索路径中的编辑器根目录及类目名称；资产身份和不同库的同名项目保持独立。
- 按各 Blender 版本的官方菜单条件筛选渲染引擎、World、工具模式和实验性节点。升级仅重建索引，核心评分公式与关键词权重不变。
- 扩大到 194 组查询验证：178 组可直接对照的查询中，首条或空结果一致率由 94.4% 提升到 99.4%，严格前列顺序一致率由 73.0% 提升到 89.3%，未遗漏采集到的原生结果。拼音与跨语言增强另行测试，不计入一致率；同分项、去重及补充节点仍可能与原生不同。
- 在隔离的 macOS Blender 5.2.2 与 5.1.2 中验证创建、菜单条件、缓存及用户数据保留；本轮未进行 Windows 原生界面对照。新增可重复运行的扩大抽样回归测试。

### English

- Retain official Output entries when other extensions wrap their menu; evaluate only official draw callbacks, not appended third-party code.
- Resolve legacy RNA aliases and missing native variants, including vector Map Range and the Typed Bundle action. Preserve existing entry IDs, favorites, shortcuts and usage records.
- Preserve original asset catalogs and correct editor-root/category search paths without merging identities across libraries.
- Follow each Blender version's native engine, World, tool and experimental-feature menu conditions. Rebuild the index without changing the core scoring formula or keyword weights.
- Expand validation to 194 queries. Across 178 directly comparable cases, first-result/empty-outcome agreement improves from 94.4% to 99.4%, strict visible-order agreement from 73.0% to 89.3%, with no captured native results missing. Pinyin and cross-language probes are excluded from parity rates; ties, deduplication and supplemental entries remain intentional differences.
- Verify creation, menu conditions, caching and user-data preservation in isolated macOS Blender 5.2.2 and 5.1.2. No fresh Windows native-UI comparison in this round. Add a repeatable expanded-sample regression suite.

## 1.4.5

<!-- node-console-summary: {"zh":"搜索排序与中文响应优化","en":"Search ranking and Chinese input speed"} -->

### 中文

- 用基于 Blender 官方源码的匹配与排序取代关键词固定顺序表；读取当前编辑器的官方菜单路径及搜索权重，支持跨单词缩写、拼写容错及词序判断。
- 搜索排序与显示类目、颜色及双语格式分离。索引独立保存官方中英文路径，构建时不修改用户界面语言；缓存增加渲染引擎、材质用途等上下文，避免跨上下文复用错误权重。
- 保留中文、全拼、首字母、相关收藏置顶及空输入可拖动快捷列表。官方菜单外的补充节点排在原生匹配之后；本地资产节点参与路径排序，同名不同库仍保持独立身份。
- 保留原有节点标识和用户数据；升级仅重建索引。搜索增强与收藏属于有意的原生差异，完全同分项和不同资源环境仍可能产生顺序差别。
- 减少输入时不再使用的旧匹配计算；输入法组词中的拼音可即时预览节点或组合点，确认后使用中文检索，取消组词则恢复原列表。启用后提前准备中文字体，降低首次显示中文结果时的停顿。
- 更新版本下拉菜单在版本号后的括号内显示简短更新重点，补齐 1.3.0 起的历史版本，保留当前、旧正式版及测试版提示；后续版本可直接读取 Release 中的摘要，不增加联网请求或状态行。

### English

- Replace fixed keyword ordering with Blender-source-based matching and ranking, using editor-specific official menu paths and weights, word initials, typo tolerance and query word order.
- Separate ranking metadata from category colors and bilingual presentation. Build independent English/Chinese paths without changing UI language; include render engine and editor purpose in index invalidation.
- Preserve Chinese, pinyin, initials, relevant favorite boosting and draggable empty-query shortcuts. Rank supplemental nodes after native matches and include local asset paths while retaining distinct library identities.
- Preserve entry identifiers and user data; rebuild only the index. Enhancements and favorites intentionally extend native behavior, while tied scores and differing resource environments can still change ordering.
- Remove unused legacy matching work from each input update. Preview IME composition without committing it, refresh with confirmed Chinese, and restore results on cancellation. Prepare the CJK font after enabling to reduce the first Chinese result-list stall.
- Add brief highlights in parentheses after update versions, covering historical releases from 1.3.0 onward while preserving installed/older stable/prerelease labels. Read future highlights from release metadata without extra requests or layout rows.

## 1.4.4

### 中文

- macOS 搜索框中的纯英文及未上屏拼音下移两个缩放单位；中文、中英混排、占位文字及 Windows 位置保持不变。
- 复用已完成的节点索引及拼音数据，减少重启后的首次搜索准备耗时和后续重复开窗开销；继续检查节点可用性、资产文件及当前项目的节点组变化，不重置收藏、快捷节点或使用权重。
- 索引缓存升级后会重建一次；后续已缓存的打开流程不再重复解析菜单和翻译，也不重复加入 Zone 条目。实测范围为 macOS 上的 Blender 5.2.2 LTS 和 5.1.2。

### English

- Lower macOS Latin input and Latin IME preedit by two scaled units, preserving CJK/mixed input, placeholders and Windows positioning.
- Reuse completed node indexes and pinyin data to reduce first-open preparation and repeated-open overhead, retaining capability checks, live asset/group validation and existing user data.
- Rebuild the index once after the cache upgrade; subsequent cached opens skip menu/translation reconstruction and do not duplicate zone entries. Tested on macOS with Blender 5.2.2 LTS and 5.1.2.

## 1.4.3

### 中文

- 更新检查、下载和错误状态直接显示在版本号后方，不再增加状态行；固定更新区控件占位，避免状态变化推动下方布局。
- 保持 1.4.2 的左右分栏和 Beta 复选框位置，收紧复选框后的留白，让版本选择框向左延伸；右侧操作按钮保持固定占位，窄窗口仍使用固定的双行布局。
- 优化「添加快捷节点」：将快捷列表、编辑器归属和显示名称合并为一次原子保存，仅复制变动字段，不再反复深拷贝整个节点索引；重复添加无变化时不写盘。保存失败时明确报错，不清空搜索文字。
- Windows 搜索框内中文及中文组词预览在 1.4.2 基础上再上移一个缩放像素；英文、占位文字和 macOS 不变。

### English

- Keep update/check/download/error status inline after the version, with stable control reservations so status changes do not push preferences downward.
- Keep the 1.4.2 half-width columns and Beta checkbox anchor; reclaim the gap after Beta for the release selector. Reserve stable space for the right-side actions and retain a two-row fallback in narrow windows.
- Save shortcut identifiers, editor scope and labels in one atomic transaction, copying only changed fields instead of entire node indexes. Identical additions skip disk writes; failures report an error and retain the query.
- Raise Windows CJK input and CJK preedit by one additional scaled pixel compared with 1.4.2; leave Latin input, placeholders and macOS unchanged.

## 1.4.2

### 中文

- Windows 搜索框内中文及中英混排文字上移一个缩放像素，包含中文组词预览；英文、占位文字及 macOS 原有位置保持不变。
- 用户已在 Windows 实机确认中文输入上屏和节点检索；其他输入法、显示缩放、多显示器及完整焦点/放置流程仍需进一步验证。本版作为正式版发布，无需勾选 Beta 即可检查更新。
- 收录 Beta 版的灰度组合点模式标签、最近三个版本选择和防止默认降级的更新逻辑。
- 修正组合点保存窗口的类目过滤：按当前编辑器列出适用类目，滤镜、遮罩、扭曲仅出现在合成节点中；补全颜色、矢量、纹理、工具等适用项。不改写已有组合点的分类。
- 节点与组合点的右键菜单从鼠标位置展开，仅在触及编辑器边缘时调整位置，不再受搜索面板高度限制。
- 更新栏与下方双列布局对齐，扩大带文字的更新按钮；窄窗口自动分行。
- 版本下拉菜单新增「其他版本」，打开 GitHub Releases 页面，同时保留当前选择，不自动下载或安装。

### English

- Raise Windows CJK/mixed input and CJK preedit by one scaled pixel; leave Latin input, placeholders and macOS positioning unchanged.
- A user confirmed Chinese input and node search on a real Windows system. Broader IME, DPI, multi-monitor, focus and placement coverage remains unverified. Publish as stable, available without Beta opt-in.
- Include the Beta's gray Snippet Node badge, latest-three version selector and protection against defaulting to a downgrade.
- Filter snippet categories by the originating node editor, keeping Filter/Mask/Distort compositor-only and restoring applicable shared categories without rewriting saved snippets.
- Anchor node/snippet context menus at the pointer, constrained only by editor edges rather than search-panel height.
- Align the updater with the two-column preferences layout and enlarge its labeled update button, retaining a narrow-window fallback.
- Add Other Versions to the version selector, opening GitHub Releases without changing the selected installation target or starting a download.

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
