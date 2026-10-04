"""Build a local-only package and validation report from successful Blender runs."""
import ast
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    '几何节点': 'https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/',
    '合成器': 'https://developer.blender.org/docs/release_notes/5.2/compositor/',
    '界面与节点编辑器': 'https://developer.blender.org/docs/release_notes/5.2/user_interface/',
    '渲染': 'https://developer.blender.org/docs/release_notes/5.2/rendering/',
    '物理': 'https://developer.blender.org/docs/release_notes/5.2/physics/',
    'Python API': 'https://developer.blender.org/docs/release_notes/5.2/python_api/',
    'API 变更': 'https://docs.blender.org/api/5.2/change_log.html',
}


def main():
    reports = [json.loads(Path(path).read_text(encoding='utf-8')) for path in sys.argv[1:]]
    assert len(reports) == 2 and all(not report['failures'] for report in reports)
    assert reports[0]['version'].startswith('5.2.')
    version = next(ast.literal_eval(node.value) for node in ast.parse((ROOT / '__init__.py').read_text()).body
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ADDON_VERSION' for t in node.targets))
    lines = [f'# Node Console {version} 验证报告', '',
             '## 环境与范围', '',
             '工作基线为干净的 `main` / `cae84b5`（1.1.2），未发现已有 1.1.3 修改。旧交接文件描述 0.8.25，仅作历史参考。',
             '5.2.2 从 Blender 官方发布服务器下载，只读挂载临时目录，不替换本机 5.1.2；全部测试使用 `--background --factory-startup`，测试配置写入临时目录。',
             '5.2.2 macOS arm64 镜像 SHA256 已与官方清单核对：`dc4125399b8bfefe283cc1624d6cfc7809d1cac20ace51072127eb371f31f210`。', '',
             '| 实测版本 / 构建 | 几何 | 材质 | 合成 | 本地资产 |',
             '| --- | ---: | ---: | ---: | ---: |']
    for report in reports:
        counts = [str(report['trees'][tree]['node_types']) for tree in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree')]
        lines.append(f"| {report['version']} / `{report['build_hash']}` | " + ' | '.join(counts) + f" | {len(report['assets'])} |")
    lines += ['', '上表是可创建的独立 RNA 类型数量，不是本次新增数量，也不把插口、枚举模式、资产组或 Zone 组合重复计为新节点。', '',
              '## 通过项目', '',
              '- 对照实际注册类型、官方安装包添加菜单及原生 `nodes.new()`；测试覆盖索引中所有内置节点与操作属性，并通过插件自己的创建入口复测。',
              '- 所有候选可用节点的英文、中文、全拼、完整首字母、大小写、去空格搜索；所有索引节点的匹配资格。',
              '- 英文 / 简中界面生成相同的双语索引；四种显示模式；Windows/Linux 使用的 fallback 拼音分支在 macOS 上强制执行测试。',
              '- 冷索引与缓存重建的条目标识一致；保留测试收藏、快捷列表、使用数据和偏好设置。',
              '- Math、Join、Inst、Line 排序回归；5.2 枚举插口模式的实际赋值。',
              '- 自带本地资产扫描与逐项创建；两个不同库的同名组独立加载，且不覆盖本地同名组。', '',
              '## 官方译名与搜索别名', '',
              '主要译名来自每个实测 Blender 安装包中的 `datafiles/locale/zh_HANS/LC_MESSAGES/blender.mo`。节点名使用 RNA translation_context，枚举使用属性 translation_context，随后才回退至默认上下文。索引不修改界面语言。',
              '`node_search_aliases.json` 明确标记为人工检索别名；旧缓存中的历史译名作为兼容别名保留。未把手册译名或人工别名宣称为官方 UI 译名。本次候选内置节点均能从 5.2.2 官方词典取得简中名称。', '',
              '## 候选逐项核对', '',
              'G = GeometryNodeTree，S = ShaderNodeTree，C = CompositorNodeTree。表中只列当前可创建的编辑器；缺席不代表猜测出的 ID。', '',
              '| 英文 / 官方简中 | 实际 RNA ID | 编辑器 | 全拼 / 首字母 |',
              '| --- | --- | --- | --- |']
    aliases = {'GeometryNodeTree': 'G', 'ShaderNodeTree': 'S', 'CompositorNodeTree': 'C'}
    for label, trees in reports[0]['candidates'].items():
        by_id = {}
        for tree, item in trees.items():
            by_id.setdefault(item['id'], []).append((tree, item))
        for node_id, items in by_id.items():
            item = items[0][1]
            lines.append(f"| {label} / {item['chinese']} | `{node_id}` | {', '.join(aliases[t] for t, _ in items)} | `{item['pinyin']}` / `{item['initials']}` |")
    lines += ['', '## 相对 5.1.2 的可创建类型变化', '',
              '以下是相同测试流程下，5.2.2 相对 5.1.2 在各编辑器新增的可创建类型；包含既有节点扩展编辑器支持，不等于全部是全新节点。', '']
    for tree, info in reports[0]['trees'].items():
        extra = sorted(set(info['node_ids']) - set(reports[1]['trees'][tree]['node_ids']))
        lines += [f'### {tree}（{len(extra)}）', '', ', '.join(f'`{name}`' for name in extra), '']
    lines += ['', '## 跨编辑器与实验性说明', '',
              '- Scene Time 在材质中实际为 `GeometryNodeInputSceneTime`，合成器仍为 `CompositorNodeSceneTime`。',
              '- 合成器的矩阵、旋转、字符串、Font、Warning 与摄像机/物体输入通过真实创建核验；不依赖类型前缀。Font 在当前 5.2.2 材质树不可创建，因此不展示。',
              '- XPBD Solver 在官方 5.2.2 默认出厂设置下已注册、菜单可见且可创建。该构建没有单独的 XPBD 实验开关；物理系统仍被官方标记为实验性，这不构成数值模拟正确性验证。',
              '- 官方安装包 `_bpy_types.py` 中继承的 GeometryNode / ShaderNode poll 仍按单一编辑器判断，和原生跨编辑器支持不一致。插件只把节点自身的 Python poll 当作额外限制，再用原生创建（含原生 poll）核验。',
              '- Get/Set Geometry Bundle、Field to List、Get List Item、List Length 在 5.1.2 中也存在可创建类型；不能全计为 5.2 首次新增。',
              '- Principled BSDF 的 Thin Wall、Capture Attribute 的 Selection、Stabilize 2D 的 Frame、Levels 的 Min/Max 等是既有节点的插口变化，没有伪造独立节点。', '',
              '## 资产', '',
              '3D to Screen Space、Screen to 3D Space、Transform and Project、Project with Depth、Film Grain、Hair/Cloth Dynamics 均作为真实 `.blend` 资产组扫描并创建。Principal Component Analysis 对应实际资产名 `Principal Components` 和 `Geometry Principal Components`，使用人工搜索别名支持 PCA / 主成分分析。',
              '5.2 的 asset_libraries 活动索引变化不影响本插件：插件枚举 `preferences.filepaths.asset_libraries` 的实际路径，不读取 active_asset_library 索引。远程库只处理已存在的本地文件；在线目录发现与下载不在本次范围。升级后手动刷新资产索引以发现新安装版本的自带库。', '',
              '## 缓存与用户数据', '',
              '运行缓存键包含插件版本、INDEX_SCHEMA、Blender 完整版本及构建哈希、树类型/用途、实验开关和资产签名。旧 bundled cache 仅作为保留旧 ID/变体的种子，每条重新做当前能力验证和翻译；当前菜单与注册类型始终合并。旧收藏与快捷列表不清除、不重写，非索引设置字段原样保留。', '',
              '## 未验证项', '',
              '- 未进行 Windows/Linux 原生 Blender 运行、5.2.0/5.2.1 或早于 5.1.2 的实机测试；fallback 分支测试不能冒充跨平台实机测试。',
              '- 未进行所有节点的渲染/数值输出、交互放置、第三方自定义节点、自定义远程资产服务的完整测试。',
              '- 索引数量以本报告构建为准；其他构建及用户实验开关变化时按实际可创建性动态变化。', '',
              '## 复测', '',
              '使用 Blender `--background --factory-startup --python-exit-code 1 --python tools/test_blender_index.py -- /tmp/report.json`。注册类型与官方译名单独审计使用 `tools/audit_blender.py`。测试不会读取真实 Node Console 设置。', '',
              '## 官方依据', '']
    lines += [f'- [{name}]({url})' for name, url in SOURCES.items()]
    (ROOT / f'VALIDATION_{version}.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    output = ROOT / f'Node_Console_{version}.zip'
    files = ('__init__.py', 'node_registry.py', 'node_search_aliases.json', 'node_console_builtin_cache.json',
             'README.md', 'CHANGELOG.md', f'VALIDATION_{version}.md', 'LICENSE')
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(ROOT / name, 'Node_Console/' + name)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {'Node_Console/' + name for name in files}
    print(output.name, hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
