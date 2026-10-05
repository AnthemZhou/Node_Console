# Node Console 1.2.1 验证报告

日期：2026-10-05。基线：1.2.0 安装包。测试平台：macOS arm64。

## 修复范围

- 为 24 个 SHADER 节点与 Script 增加专用色板，重建索引时从当前 Blender 实例取得对应原生标签，补齐旧缓存种子中的缺失信息。
- Curve Length 与 String to Curves 使用几何类颜色；Light Output 与 Line Style Output 使用输出类暗红色。
- FILTER、MATTE、DISTORT 直接映射到已有合成类别色板，Split Toning 不再落入通用颜色。
- Shader 类组合点同步使用独立着色器绿色；没有重写组合点文件。
- 保留 Geometry Viewer 的中性搜索颜色，以及组输入/输出、Simulation、For Each、Closure 等既有特殊配色。搜索结果没有实际活动节点，不能按 OUTPUT 标签把全部结果改成暗红色。

## 实际运行结果

| Blender / 构建 | 原生搜索条目实际创建及配色比对 | 官方本地资产实际创建及配色比对 | 相对 1.2.0 配色变化 | 失败 |
| --- | ---: | ---: | ---: | ---: |
| 5.2.2 LTS / `d13f752e3b9c` | 1,063 | 83 | 30 | 0 |
| 5.1.2 / `ec6e62d40fa9` | 974 | 65 | 30 | 0 |

原生条目包含运算设置变体，不是独立 RNA 类型计数。30 项为 29 个原生条目和 Split Toning 资产；组合点类别配色另做断言，不重复加入节点统计。

- 与同一 Blender 构建下的 1.2.0 逐条对比，确认条目标识集合不变；目标修复之外的配色保持不变，包括 ZONE 入口。资产对照加载后的原生 `color_tag`，不根据英文名称猜分类。
- 冷索引与热缓存重建配色一致。新版本号已进入原有索引缓存键，升级会重建运行缓存，不清除收藏、快捷节点、权重或设置。
- 两个版本的完整 `test_blender_index.py` 均通过：实际注册类型与菜单覆盖、插件创建入口、节点设置、双语/全拼/首字母搜索、排序、显示模式、缓存和用户数据保留、同名资产库隔离。
- Shader 组合点映射和无目录资产的 FILTER 类别名称另有回归断言。
- `Node_Console_1.2.1.zip` 已在两版 Blender 的独立临时目录通过安装、启用、三种节点树索引、禁用、重新启用与再次禁用测试。ZIP 使用 `Node_Console/` 顶层目录，不包含 Display 素材或用户设置。

## 界面核验依据

修复前已在独立 Blender 5.2.2 节点编辑器逐项显示检查 29 种新增原生类型、41 项已有类型跨编辑器支持、24 个 SHADER 节点及其他问题节点；83 个本地资产的标题色也全部目视确认。Split Toning 在展开与折叠时均为滤镜紫色。

1.2.1 修复后的全量验证采用真实节点创建和插件配色函数比对，没有声称重新逐个手工截图所有搜索变体。插件色板保留低饱和度风格，不要求与用户 Blender 主题 RGB 完全相同。

## 隔离与限制

测试均使用独立 `--background --factory-startup` 进程和临时设置目录，没有操作用户原有项目或快捷键配置。沙箱内 Blender 曾在 Metal 初始化时崩溃，发生在 Python 测试执行前；随后在获准的沙箱外独立出厂配置进程中完成上述测试。

未验证 Windows/Linux 原生运行、其他 Blender 构建、全部节点数值/渲染结果、第三方资产、自定义主题与完整交互放置流程。本次没有新增节点，仅修正分类配色。

## 复测

- 配色：`Blender --background --factory-startup --python-exit-code 1 --python tools/test_node_colors.py -- /tmp/colors.json`，需在工程根目录保留 `Node_Console_1.2.0.zip` 基线安装包。
- 检索与创建：`Blender --background --factory-startup --python-exit-code 1 --python tools/test_blender_index.py -- /tmp/index.json`。
- 安装包：为 `BLENDER_USER_SCRIPTS` 和 `BLENDER_USER_CONFIG` 指定独立临时目录，再执行 `tools/test_package_install.py`，参数为当前版本 ZIP 路径。
