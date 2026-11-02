"""Language-specific usability probes, distinct from exact-name reachability."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import bpy

ROOT = Path(__file__).resolve().parents[1]
PROBES = {
    'ja_JP': [('のいず', 'ShaderNodeTexNoise'), ('ﾉｲｽﾞ', 'ShaderNodeTexNoise'),
              ('のいずてく', 'ShaderNodeTexNoise'), ('めっしゅらいん', 'GeometryNodeMeshLine')],
    'ko_KR': [('노이즈텍', 'ShaderNodeTexNoise'), ('ㄴㅇㅈ', 'ShaderNodeTexNoise'),
              ('노ㅇ', 'ShaderNodeTexNoise'), ('위치설', 'GeometryNodeSetPosition')],
    'ru_RU': [('объем', 'GeometryNodeMeshToVolume'), ('ОБЪЕМ', 'GeometryNodeMeshToVolume'),
              ('текстура шу', 'ShaderNodeTexNoise'), ('полож', 'GeometryNodeInputPosition')],
    'es': [('posicion', 'GeometryNodeInputPosition'), ('POSICION', 'GeometryNodeInputPosition'),
           ('geometria', 'GeometryNodeJoinGeometry'), ('rotacion', 'FunctionNodeRotateRotation')],
}
ENGLISH = ('noise', 'nt', 'niose', 'line', 'add', 'join', 'position', 'math',
           'random value', 'mix', 'blur', 'input object')


def main():
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
    bpy.context.preferences.use_preferences_save = False
    spec = importlib.util.spec_from_file_location('NCLanguageAudit', ROOT/'__init__.py', submodule_search_locations=[str(ROOT)])
    nc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = nc
    spec.loader.exec_module(nc)
    nc._settings_path = lambda: Path(os.environ['BLENDER_USER_CONFIG'])/'language-audit.json'
    nc._preferences = lambda: None
    report = dict(version=bpy.app.version_string, probes=[], english=[], native_cases=[])
    for tree_type in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
        tree = bpy.data.node_groups.new('Language audit', tree_type)
        context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_type,
            shader_type='OBJECT', id_from=bpy.context.object), engine='BLENDER_EEVEE')
        nc._search_language = lambda: 'zh_HANS'
        nc._clear_search_caches()
        nc._rebuild_search_entries(context)
        english = {q: [e.identifier for e in nc._search_entries(q, set())[:5]] for q in ENGLISH}
        for language, probes in PROBES.items():
            nc._search_language = lambda: language
            nc._clear_search_caches()
            nc._rebuild_search_entries(context)
            for query, expected in probes:
                if tree_type != 'GeometryNodeTree':
                    continue
                found = nc._search_entries(query, set())
                names = [e.english for e in found[:5]]
                report['probes'].append(dict(language=language, query=query, expected=expected,
                    pass_top5=any(e.node_type == expected for e in found[:5]), first=names))
            for query in ENGLISH:
                found = [e.identifier for e in nc._search_entries(query, set())[:5]]
                report['english'].append(dict(tree=tree_type, language=language, query=query,
                    expected=english[query], actual=found, same=found==english[query],
                    same_prefix=found[:len(english[query])]==english[query]))
            targets = ('Noise Texture', 'Position', 'Join Geometry', 'Set Position', 'Mesh Line') if tree_type=='GeometryNodeTree' else (
                ('Principled BSDF', 'Noise Texture', 'Texture Coordinate', 'Layer Weight')
                if tree_type=='ShaderNodeTree' else ('Blur', 'Glare', 'Transform', 'Lens Distortion'))
            for name in targets:
                entry = next(e for e in nc.NODE_SEARCH_ENTRIES if e.english==name)
                report['native_cases'].append(dict(tree=tree_type, language=language, query=entry.chinese,
                    engine='BLENDER_EEVEE', shader='OBJECT', group='baseline'))
        bpy.data.node_groups.remove(tree)
    path = Path(sys.argv[sys.argv.index('--')+1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    path.with_name(path.stem+'-native-cases.json').write_text(json.dumps(report['native_cases'],ensure_ascii=False,indent=2))
    print('LANGUAGE_EXPERIENCE', sum(x['pass_top5'] for x in report['probes']), '/', len(report['probes']),
          'ENGLISH_TOP5', sum(x['same'] for x in report['english']), '/', len(report['english']), flush=True)
    print(json.dumps(report['probes'],ensure_ascii=False,indent=2),flush=True)
    if '--verify' in sys.argv:
        assert all(x['pass_top5'] for x in report['probes'])
        assert all(x['same_prefix'] for x in report['english'])


if __name__=='__main__':
    main()
