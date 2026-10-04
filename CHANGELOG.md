# Changelog

## 1.1.3

### 中文

- 补齐 Blender 5.2 节点检索：几何捆包、列表、集合子级、声音采样、点聚集与合并、网格倒角、属性处理、NURBS、字符串等；同时补入注册类型审计发现的整数矢量、标签过滤及嵌套捆包路径等条目。
- 修复跨编辑器节点遗漏：材质节点中的布尔、整数、矢量与场景时间，以及合成器中的摄像机、物体、矩阵、旋转、字符串、字体和警告节点。合成器新增空白图像、字符串转图像。
- 不再按节点类前缀或继承的 Python 基类 poll 推断编辑器支持，改用当前节点树、节点自身限制和原生创建能力检查。缓存命中后仍补全当前版本添加菜单。
- 中文译名读取当前 Blender 官方简中词典，尊重 RNA 翻译上下文，无需更改用户界面语言。人工别名与官方译名单独维护，旧搜索别名继续保留。
- 修复完整拼音首字母不能稳定命中的问题；改善空格、大小写、多音字和包含英文缩写的拼音处理；支持 5.2 的枚举插口搜索变体。
- 搜索缓存按 Blender 版本、构建、索引结构和实验开关失效。保留已有收藏、快捷节点、使用数据及偏好设置，不改快捷键逻辑。
- 修复资产扫描时名称被载入重命名污染，以及同名不同库资产添加时串用的问题。保留本地资产扫描机制，不增加在线资产下载系统。
- 实测 Blender 5.2.2 LTS、5.1.2。详细节点与验证范围见 `VALIDATION_1.1.3.md`。

### English

- Completed runtime discovery for Blender 5.2 geometry, list, string, attribute, NURBS and compositor nodes, including registered types not covered by the initial candidate list.
- Fixed cross-editor omissions in shaders and compositing. Native creation checks replace assumptions based on class prefixes or inherited Python poll methods.
- Read official Simplified Chinese catalogs with RNA contexts without changing the UI language. Keep editorial aliases separate from official names.
- Fixed complete pinyin-initial matching, whitespace handling and selected polyphonic readings. Added support for searchable enum-socket variants.
- Versioned the index by Blender build, schema and experimental settings while preserving user data and existing shortcuts.
- Fixed asset source-name preservation and same-name library isolation. Undownloaded online assets remain outside the local index.
- Tested on Blender 5.2.2 LTS and 5.1.2; see the validation report for exact coverage and limitations.
