# Node Console 1.2.0 验证报告

## 环境与范围

工作基线为干净的 `main` / `cae84b5`（1.1.2），开发开始时没有未提交修改。旧交接文件描述 0.8.25，仅作历史参考。
5.2.2 从 Blender 官方发布服务器下载，只读挂载临时目录，不替换本机 5.1.2；全部测试使用 `--background --factory-startup`，测试配置写入临时目录。
5.2.2 macOS arm64 镜像 SHA256 已与官方清单核对：`dc4125399b8bfefe283cc1624d6cfc7809d1cac20ace51072127eb371f31f210`。

| 实测版本 / 构建 | 几何 | 材质 | 合成 | 本地资产 |
| --- | ---: | ---: | ---: | ---: |
| 5.2.2 LTS / `d13f752e3b9c` | 360 | 118 | 168 | 83 |
| 5.1.2 / `ec6e62d40fa9` | 333 | 112 | 122 | 65 |

上表是可创建的独立 RNA 类型数量，不是本次新增数量，也不把插口、枚举模式、资产组或 Zone 组合重复计为新节点。

## 通过项目

- 对照实际注册类型、官方安装包添加菜单及原生 `nodes.new()`；测试覆盖索引中所有内置节点与操作属性，并通过插件自己的创建入口复测。
- 所有候选可用节点的英文、中文、全拼、完整首字母、大小写、去空格搜索；所有索引节点的匹配资格。
- 英文 / 简中界面生成相同的双语索引；四种显示模式；Windows/Linux 使用的 fallback 拼音分支在 macOS 上强制执行测试。
- 冷索引与缓存重建的条目标识一致；保留测试收藏、快捷列表、使用数据和偏好设置。
- Math、Join、Inst、Line 排序回归；5.2 枚举插口模式的实际赋值。
- 自带本地资产扫描与逐项创建；两个不同库的同名组独立加载，且不覆盖本地同名组。

## 官方译名与搜索别名

主要译名来自每个实测 Blender 安装包中的 `datafiles/locale/zh_HANS/LC_MESSAGES/blender.mo`。节点名使用 RNA translation_context，枚举使用属性 translation_context，随后才回退至默认上下文。索引不修改界面语言。
`node_search_aliases.json` 明确标记为人工检索别名；旧缓存中的历史译名作为兼容别名保留。未把手册译名或人工别名宣称为官方 UI 译名。本次候选内置节点均能从 5.2.2 官方词典取得简中名称。

## 候选逐项核对

G = GeometryNodeTree，S = ShaderNodeTree，C = CompositorNodeTree。表中只列当前可创建的编辑器；缺席不代表猜测出的 ID。

| 英文 / 官方简中 | 实际 RNA ID | 编辑器 | 全拼 / 首字母 |
| --- | --- | --- | --- |
| Get Geometry Bundle / 获取几何体捆包 | `GeometryNodeGetGeometryBundle` | G | `huoqujihetikunbao` / `hqjhtkb` |
| Set Geometry Bundle / 设置几何体捆包 | `GeometryNodeSetGeometryBundle` | G | `shezhijihetikunbao` / `szjhtkb` |
| Field to List / 场 转为 列表 | `GeometryNodeFieldToList` | G | `changzhuanweiliebiao` / `czwlb` |
| Closure to List / 闭包 转为 列表 | `GeometryNodeClosureToList` | G | `bibaozhuanweiliebiao` / `bbzwlb` |
| List Length / 列表长度 | `GeometryNodeListLength` | G | `liebiaochangdu` / `lbcd` |
| Get List Item / 获取列表项目 | `GeometryNodeListGetItem` | G | `huoquliebiaoxiangmu` / `hqlbxm` |
| Filter List / 过滤列表 | `GeometryNodeFilterList` | G | `guolvliebiao` / `gllb` |
| Sort List / 排序列表 | `GeometryNodeSortList` | G | `paixuliebiao` / `pxlb` |
| Collection Children / 集合子级 | `GeometryNodeCollectionChildren` | G | `jiheziji` / `jhzj` |
| Sample Sound Frequencies / 采样声音频率 | `GeometryNodeSampleSoundFrequencies` | G | `caiyangshengyinpinlv` / `cysypl` |
| Merge Points / 合并点 | `GeometryNodeMergePoints` | G | `hebingdian` / `hbd` |
| Cluster by Distance / 按距离聚集 | `GeometryNodeClusterByDistance` | G | `anjulijuji` / `ajljj` |
| Cluster by Connected / 按连接性聚集 | `GeometryNodeClusterByConnected` | G | `anlianjiexingjuji` / `aljxjj` |
| Mesh Bevel / 网格倒角 | `GeometryNodeMeshBevel` | G | `wanggedaojiao` / `wgdj` |
| Rename Attribute / 重命名属性 | `GeometryNodeRenameAttribute` | G | `chongmingmingshuxing` / `cmmsx` |
| Get Attribute Names / 获取属性名称 | `GeometryNodeGetAttributeNames` | G | `huoqushuxingmingcheng` / `hqsxmc` |
| Transfer Attributes / 传递属性 | `GeometryNodeTransferAttributes` | G | `chuandishuxing` / `cdsx` |
| Set NURBS Order / 设置 NURBS 阶数 | `GeometryNodeSetNURBSOrder` | G | `shezhinurbsjieshu` / `sznjs` |
| Set NURBS Weight / 设置 NURBS 权重 | `GeometryNodeSetNURBSWeight` | G | `shezhinurbsquanzhong` / `sznqz` |
| Instance Reference / 实例引用 | `GeometryNodeInputInstanceReference` | G | `shiliyinyong` / `slyy` |
| Get Geometry Component / 获取几何组件 | `GeometryNodeGetGeometryComponent` | G | `huoqujihezujian` / `hqjhzj` |
| XPBD Solver / XPBD 解算器 | `GeometryNodeXPBDSolver` | G | `xpbdjiesuanqi` / `xjsq` |
| Trim String / 修剪字符串 | `FunctionNodeTrimString` | G, C | `xiujianzifuchuan` / `xjzfc` |
| Reverse String / 反转字符串 | `FunctionNodeReverseString` | G, C | `fanzhuanzifuchuan` / `fzzfc` |
| Set String Case / 设置字符串大小写 | `FunctionNodeSetStringCase` | G, C | `shezhizifuchuandaxiaoxie` / `szzfcdxx` |
| Split String / 拆分字符串 | `FunctionNodeSplitString` | G | `chaifenzifuchuan` / `cfzfc` |
| Implicit Conversion / 隐式转换 | `NodeImplicitConversion` | G, S, C | `yinshizhuanhuan` / `yszh` |
| Menu / 菜单 | `FunctionNodeInputMenu` | G, S, C | `caidan` / `cd` |
| Font / 字体 | `GeometryNodeInputFont` | G, C | `ziti` / `zt` |
| Scene Time / 场景时间 | `GeometryNodeInputSceneTime` | G, S | `changjingshijian` / `cjsj` |
| Scene Time / 场景时间 | `CompositorNodeSceneTime` | C | `changjingshijian` / `cjsj` |
| Boolean / 布尔 | `FunctionNodeInputBool` | G, S, C | `buer` / `be` |
| Integer / 整数 | `FunctionNodeInputInt` | G, S, C | `zhengshu` / `zs` |
| Vector / 矢量 | `FunctionNodeInputVector` | G, S, C | `shiliang` / `sl` |
| Active Camera / 活动摄像机 | `GeometryNodeInputActiveCamera` | G, C | `huodongshexiangji` / `hdsxj` |
| Camera Info / 摄像机信息 | `GeometryNodeCameraInfo` | G, C | `shexiangjixinxi` / `sxjxx` |
| Object / 物体 | `GeometryNodeInputObject` | G, C | `wuti` / `wt` |
| Object Info / 物体信息 | `GeometryNodeObjectInfo` | G, C | `wutixinxi` / `wtxx` |
| Object Info / 物体信息 | `ShaderNodeObjectInfo` | S | `wutixinxi` / `wtxx` |
| Warning / 警告 | `GeometryNodeWarning` | G, C | `jinggao` / `jg` |
| Integer Vector / 整数矢量 | `FunctionNodeInputIntVector` | G, C | `zhengshushiliang` / `zssl` |
| Get Nested Bundle Paths / 获取嵌套捆包路径 | `NodeGetNestedBundlePaths` | G | `huoquqiantaokunbaolujing` / `hqqtkblj` |
| Tag Filter / 标签过滤 | `GeometryNodeTagFilter` | G | `biaoqianguolv` / `bqgl` |
| Blank Image / 空白图像 | `CompositorNodeBlankImage` | C | `kongbaituxiang` / `kbtx` |
| String To Image / 字符串 转为 图像 | `CompositorNodeStringToImage` | C | `zifuchuanzhuanweituxiang` / `zfczwtx` |

## 相对 5.1.2 的可创建类型变化

以下是相同测试流程下，5.2.2 相对 5.1.2 在各编辑器新增的可创建类型；包含既有节点扩展编辑器支持，不等于全部是全新节点。

### GeometryNodeTree（27）

`FunctionNodeInputIntVector`, `FunctionNodeInputMenu`, `FunctionNodeReverseString`, `FunctionNodeSetStringCase`, `FunctionNodeSplitString`, `FunctionNodeTrimString`, `GeometryNodeClosureToList`, `GeometryNodeClusterByConnected`, `GeometryNodeClusterByDistance`, `GeometryNodeCollectionChildren`, `GeometryNodeFilterList`, `GeometryNodeGetAttributeNames`, `GeometryNodeGetGeometryComponent`, `GeometryNodeInputFont`, `GeometryNodeInputInstanceReference`, `GeometryNodeMergePoints`, `GeometryNodeMeshBevel`, `GeometryNodeRenameAttribute`, `GeometryNodeSampleSoundFrequencies`, `GeometryNodeSetNURBSOrder`, `GeometryNodeSetNURBSWeight`, `GeometryNodeSortList`, `GeometryNodeTagFilter`, `GeometryNodeTransferAttributes`, `GeometryNodeXPBDSolver`, `NodeGetNestedBundlePaths`, `NodeImplicitConversion`

### ShaderNodeTree（6）

`FunctionNodeInputBool`, `FunctionNodeInputInt`, `FunctionNodeInputMenu`, `FunctionNodeInputVector`, `GeometryNodeInputSceneTime`, `NodeImplicitConversion`

### CompositorNodeTree（46）

`CompositorNodeBlankImage`, `CompositorNodeStringToImage`, `FunctionNodeAlignRotationToVector`, `FunctionNodeAxesToRotation`, `FunctionNodeAxisAngleToRotation`, `FunctionNodeCombineMatrix`, `FunctionNodeEulerToRotation`, `FunctionNodeFindInString`, `FunctionNodeFormatString`, `FunctionNodeInputIntVector`, `FunctionNodeInputMenu`, `FunctionNodeInputRotation`, `FunctionNodeInputSpecialCharacters`, `FunctionNodeInputString`, `FunctionNodeInvertMatrix`, `FunctionNodeInvertRotation`, `FunctionNodeMatchString`, `FunctionNodeMatrixDeterminant`, `FunctionNodeMatrixMultiply`, `FunctionNodeProjectPoint`, `FunctionNodeQuaternionToRotation`, `FunctionNodeReplaceString`, `FunctionNodeReverseString`, `FunctionNodeRotateRotation`, `FunctionNodeRotateVector`, `FunctionNodeRotationToAxisAngle`, `FunctionNodeRotationToEuler`, `FunctionNodeRotationToQuaternion`, `FunctionNodeSeparateMatrix`, `FunctionNodeSetStringCase`, `FunctionNodeSliceString`, `FunctionNodeStringLength`, `FunctionNodeStringToValue`, `FunctionNodeTransformDirection`, `FunctionNodeTransformPoint`, `FunctionNodeTransposeMatrix`, `FunctionNodeTrimString`, `FunctionNodeValueToString`, `GeometryNodeCameraInfo`, `GeometryNodeInputActiveCamera`, `GeometryNodeInputFont`, `GeometryNodeInputObject`, `GeometryNodeObjectInfo`, `GeometryNodeSwitch`, `GeometryNodeWarning`, `NodeImplicitConversion`


## 跨编辑器与实验性说明

- Scene Time 在材质中实际为 `GeometryNodeInputSceneTime`，合成器仍为 `CompositorNodeSceneTime`。
- 合成器的矩阵、旋转、字符串、Font、Warning 与摄像机/物体输入通过真实创建核验；不依赖类型前缀。Font 在当前 5.2.2 材质树不可创建，因此不展示。
- XPBD Solver 在官方 5.2.2 默认出厂设置下已注册、菜单可见且可创建。该构建没有单独的 XPBD 实验开关；物理系统仍被官方标记为实验性，这不构成数值模拟正确性验证。
- 官方安装包 `_bpy_types.py` 中继承的 GeometryNode / ShaderNode poll 仍按单一编辑器判断，和原生跨编辑器支持不一致。插件只把节点自身的 Python poll 当作额外限制，再用原生创建（含原生 poll）核验。
- Get/Set Geometry Bundle、Field to List、Get List Item、List Length 在 5.1.2 中也存在可创建类型；不能全计为 5.2 首次新增。
- Principled BSDF 的 Thin Wall、Capture Attribute 的 Selection、Stabilize 2D 的 Frame、Levels 的 Min/Max 等是既有节点的插口变化，没有伪造独立节点。

## 资产

3D to Screen Space、Screen to 3D Space、Transform and Project、Project with Depth、Film Grain、Hair/Cloth Dynamics 均作为真实 `.blend` 资产组扫描并创建。Principal Component Analysis 对应实际资产名 `Principal Components` 和 `Geometry Principal Components`，使用人工搜索别名支持 PCA / 主成分分析。
5.2 的 asset_libraries 活动索引变化不影响本插件：插件枚举 `preferences.filepaths.asset_libraries` 的实际路径，不读取 active_asset_library 索引。远程库只处理已存在的本地文件；在线目录发现与下载不在本次范围。升级后手动刷新资产索引以发现新安装版本的自带库。

## 缓存与用户数据

运行缓存键包含插件版本、INDEX_SCHEMA、Blender 完整版本及构建哈希、树类型/用途、实验开关和资产签名。旧 bundled cache 仅作为保留旧 ID/变体的种子，每条重新做当前能力验证和翻译；当前菜单与注册类型始终合并。旧收藏与快捷列表不清除、不重写，非索引设置字段原样保留。

## 未验证项

- 未进行 Windows/Linux 原生 Blender 运行、5.2.0/5.2.1 或早于 5.1.2 的实机测试；fallback 分支测试不能冒充跨平台实机测试。
- 未进行所有节点的渲染/数值输出、交互放置、第三方自定义节点、自定义远程资产服务的完整测试。
- 索引数量以本报告构建为准；其他构建及用户实验开关变化时按实际可创建性动态变化。

## 复测

使用 Blender `--background --factory-startup --python-exit-code 1 --python tools/test_blender_index.py -- /tmp/report.json`。注册类型与官方译名单独审计使用 `tools/audit_blender.py`。测试不会读取真实 Node Console 设置。

## 官方依据

- [几何节点](https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/)
- [合成器](https://developer.blender.org/docs/release_notes/5.2/compositor/)
- [界面与节点编辑器](https://developer.blender.org/docs/release_notes/5.2/user_interface/)
- [渲染](https://developer.blender.org/docs/release_notes/5.2/rendering/)
- [物理](https://developer.blender.org/docs/release_notes/5.2/physics/)
- [Python API](https://developer.blender.org/docs/release_notes/5.2/python_api/)
- [API 变更](https://docs.blender.org/api/5.2/change_log.html)
