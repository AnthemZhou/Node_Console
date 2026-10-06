# Changelog

## 1.2.2

### 中文

- 优化输入检索：复用不可变节点条目的名称、分类和拼音预处理结果；文本缓存有容量上限，收藏与排序仍实时计算。
- 避免未命中时的拼音回退重复匹配；空查询不再遍历索引。
- 索引重建复用本次节点能力检查结果，减少重复读取 Blender 运行信息；保留打开窗口时对本地节点组、资产与设置的更新。
- Blender 5.2.2 实测搜索核心中位耗时降低约 54%–59%，热索引准备耗时降低约 44%–63%；这些数据不代表整体界面帧率。
- 增加与 1.2.1 的完整搜索结果/排序对照、性能基准与缓存生命周期测试。Blender 5.2.2 与 5.1.2 共 10,935 次查询对照零差异；实测范围和数据见 `PERFORMANCE.md` 和 `VALIDATION_1.2.2.md`。不改变快捷键、收藏、使用数据或持久化格式。

### English

- Reuse immutable entry text/pinyin preprocessing with bounded text caches; evaluate favorites and ranking live.
- Reuse matches during weak-pinyin fallback and skip matching for empty queries.
- Reuse capability data within each index rebuild while retaining live group, asset and preference updates.
- Reduce measured median core search time by approximately 54%–59% and warm index preparation by 44%–63% on Blender 5.2.2; these are not GUI frame-rate measurements.
- Add baseline result/order comparisons, benchmarks and cache lifecycle regressions: 10,935 queries match 1.2.1 exactly across Blender 5.2.2 and 5.1.2. See `PERFORMANCE.md` and `VALIDATION_1.2.2.md`. Shortcuts, favorites, usage data and persistence formats are unchanged.

## 1.2.1

### 中文

- 修复 24 个 Shader 节点和 Script 节点的颜色回退，增加独立的着色器绿色与脚本青色，并从当前 Blender 实例补齐旧索引中的对应标签。
- 修正 Curve Length、String to Curves 的几何类颜色，以及 Light Output、Line Style Output 的输出类暗红色；修正 String to Curves 的 RNA 标识匹配。
- 补齐 FILTER、MATTE、DISTORT 颜色映射，修复官方 Split Toning 资产组被显示为通用颜色的问题；Shader 类组合点同步使用着色器绿色。
- 保留未激活 Geometry Viewer、组输入/输出和区域节点的特殊配色；不改快捷键、收藏、使用权重、组合点库或用户设置。
- 增加实际 Blender 节点/资产创建、颜色映射、旧版对比和缓存重建回归。版本升级自动使运行索引缓存失效，无需重置偏好设置。
- 实测 Blender 5.2.2 LTS 与 5.1.2，配色、搜索/创建、用户数据保留及 ZIP 安装启停检查均通过，详见 `VALIDATION_1.2.1.md`。

### English

- Added dedicated shader/script colors and restored their native tags in legacy index entries, fixing 24 shader nodes and Script.
- Corrected Curve Length, String to Curves, Light Output and Line Style Output colors and the String to Curves RNA match.
- Added FILTER, MATTE and DISTORT mappings, fixing the Split Toning asset fallback. Shader snippets now use shader green.
- Preserved neutral Geometry Viewer/interface colors and zone styling, without changing shortcuts or user data.
- Added real Blender color/create regression tests against 1.2.0, including warm-cache checks. The versioned runtime index rebuilds automatically.
- Tested color/search/create regressions, user-data preservation and ZIP install/enable/disable cycles on Blender 5.2.2 LTS and 5.1.2; see `VALIDATION_1.2.1.md`.

## 1.2.0

### 中文

- 补齐 Blender 5.2 节点检索：几何捆包、列表、集合子级、声音采样、点聚集与合并、网格倒角、属性处理、NURBS、字符串等；同时补入注册类型审计发现的整数矢量、标签过滤及嵌套捆包路径等条目。
- 修复跨编辑器节点遗漏：材质节点中的布尔、整数、矢量与场景时间，以及合成器中的摄像机、物体、矩阵、旋转、字符串、字体和警告节点。合成器新增空白图像、字符串转图像。
- 不再按节点类前缀或继承的 Python 基类 poll 推断编辑器支持，改用当前节点树、节点自身限制和原生创建能力检查。缓存命中后仍补全当前版本添加菜单。
- 中文译名读取当前 Blender 官方简中词典，尊重 RNA 翻译上下文，无需更改用户界面语言。人工别名与官方译名单独维护，旧搜索别名继续保留。
- 修复完整拼音首字母不能稳定命中的问题；改善空格、大小写、多音字和包含英文缩写的拼音处理；支持 5.2 的枚举插口搜索变体。
- 搜索缓存按 Blender 版本、构建、索引结构和实验开关失效。保留已有收藏、快捷节点、使用数据及偏好设置，不改快捷键逻辑。
- 修复资产扫描时名称被载入重命名污染，以及同名不同库资产添加时串用的问题。保留本地资产扫描机制，不增加在线资产下载系统。
- 实测 Blender 5.2.2 LTS、5.1.2。详细节点与验证范围见 `VALIDATION_1.2.0.md`。

### English

- Completed runtime discovery for Blender 5.2 geometry, list, string, attribute, NURBS and compositor nodes, including registered types not covered by the initial candidate list.
- Fixed cross-editor omissions in shaders and compositing. Native creation checks replace assumptions based on class prefixes or inherited Python poll methods.
- Read official Simplified Chinese catalogs with RNA contexts without changing the UI language. Keep editorial aliases separate from official names.
- Fixed complete pinyin-initial matching, whitespace handling and selected polyphonic readings. Added support for searchable enum-socket variants.
- Versioned the index by Blender build, schema and experimental settings while preserving user data and existing shortcuts.
- Fixed asset source-name preservation and same-name library isolation. Undownloaded online assets remain outside the local index.
- Tested on Blender 5.2.2 LTS and 5.1.2; see the validation report for exact coverage and limitations.
