"""Predeclared live-UI audit sample; keep extension probes out of parity rates."""

BASE = {
    'GeometryNodeTree': {
        'en_US': ['a', 's', 'set', 'get', 'math', 'vector', 'point', 'curve', 'mesh',
                  'sample', 'attribute', 'transform', 'rotate', 'scale', 'normal',
                  'random', 'compare', 'switch', 'list', 'bundle', 'simulation',
                  'noise texture', 'texture noise', 'nt', 'jion', 'realize inst', 'zzzzqqqq'],
        'zh_HANS': ['设置', '获取', '输入', '输出', '数学', '矢量', '点', '曲线', '网格',
                    '采样', '属性', '变换', '旋转', '缩放', '法线', '随机', '比较', '切换',
                    '列表', '捆绑', '模拟', '噪波', '实例', '合并', '位置', '集合', '材质'],
    },
    'ShaderNodeTree': {
        'en_US': ['a', 's', 'add', 'mix', 'math', 'vector', 'color', 'shader', 'bsdf',
                  'texture', 'image', 'noise', 'normal', 'bump', 'mapping', 'uv',
                  'fresnel', 'emission', 'transparent', 'principled', 'value',
                  'map range', 'color ramp', 'nt', 'principld', 'noise texture', 'zzzzqqqq'],
        'zh_HANS': ['添加', '混合', '运算', '矢量', '颜色', '着色器', '纹理', '图像', '噪波',
                    '法线', '凹凸', '映射', '菲涅尔', '自发光', '透明', '原理化', '值',
                    '映射范围', '颜色渐变', '几何', '坐标', '相机', '光程', '输出', '时间', '设置', '乘'],
    },
    'CompositorNodeTree': {
        'en_US': ['a', 's', 'blur', 'filter', 'color', 'mix', 'math', 'alpha', 'image',
                  'render', 'mask', 'key', 'transform', 'rotate', 'scale', 'glare',
                  'denoise', 'exposure', 'curves', 'vector', 'string', 'set alpha',
                  'alpha set', 'vb', 'blru', 'color balance', 'zzzzqqqq'],
        'zh_HANS': ['模糊', '滤镜', '颜色', '混合', '运算', '图像', '渲染', '遮罩', '抠像',
                    '变换', '旋转', '缩放', '眩光', '降噪', '曝光', '曲线', '矢量', '字符串',
                    '设置', '平衡', '亮度', '对比', '镜头', '时间', '相机', '合成', '输出'],
    },
}


def cases():
    result = []
    def add(tree, language, query, group='baseline', engine='BLENDER_EEVEE', shader='OBJECT'):
        result.append(dict(tree=tree, language=language, query=query, group=group,
                           engine=engine, shader=shader))
    for tree, languages in BASE.items():
        for language, queries in languages.items():
            for query in queries:
                add(tree, language, query)
    for engine, shader in [('BLENDER_EEVEE', 'WORLD'), ('CYCLES', 'OBJECT')]:
        for language, queries in [('en_US', ['background', 'shader', 'output', 'light']),
                                  ('zh_HANS', ['背景', '着色器', '输出', '光'])]:
            for query in queries:
                add('ShaderNodeTree', language, query, 'context', engine, shader)
    for tree in BASE:
        for query in ['zaobo', 'zbwl', 'she zhi']:
            add(tree, 'en_US', query, 'pinyin')
    for tree, language, query in [('GeometryNodeTree', 'zh_HANS', 'position'),
                                  ('GeometryNodeTree', 'zh_HANS', 'add'),
                                  ('GeometryNodeTree', 'en_US', '设置'),
                                  ('ShaderNodeTree', 'zh_HANS', 'noise'),
                                  ('ShaderNodeTree', 'en_US', '噪波'),
                                  ('CompositorNodeTree', 'zh_HANS', 'blur'),
                                  ('CompositorNodeTree', 'en_US', '模糊')]:
        add(tree, language, query, 'cross_language')
    assert len(result) == 194
    return result
