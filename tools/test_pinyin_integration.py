"""Pinyin ranking, favorites and cache invalidation with isolated fake nodes."""
import importlib.util
import os
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
spec = importlib.util.spec_from_file_location('NCPinyinIntegration', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc._preferences = lambda: None


def entry(identifier, english, chinese, category='\u5b9e\u4f8b', weight=0):
    return nc.NodeSearchEntry(identifier, 'Instance', english, chinese, english, '', 'NODE',
        menu_paths=((f'Instances \u25b8 {english}', f'{category} \u25b8 {chinese}', weight),))


def search(query, favorites=()):
    return [e.identifier for e in nc._search_entries(query, set(favorites))]


points = entry('points', 'Instance on Points', '\u5b9e\u4f8b\u5316\u4e8e\u70b9\u4e0a', weight=10)
bounds = entry('bounds', 'Instance Bounds', '\u5b9e\u4f8b\u8fb9\u754c')
random = entry('random', 'Randomize Transforms', '\u968f\u673a\u53d8\u6362')
nc.NODE_SEARCH_ENTRIES[:] = [points, bounds, random]
assert search('instance')[0] == 'points'
assert nc.SEARCH_PINYIN_INDEX is None, 'Ordinary English must not prepare pinyin paths'
expected = search('\u5b9e\u4f8b')
assert expected == ['points', 'bounds', 'random']
for query in ('shili', 'SHILI', 'shi li', '  shi  li  '):
    assert search(query) == expected
    assert search(query, ['random']) == search('\u5b9e\u4f8b', ['random'])
assert search('sl'), 'Initials remain supported'
assert search('shil'), 'Incomplete pinyin remains supported'

index = nc.SEARCH_PINYIN_INDEX
replacement = entry('collection', 'Collection Info', '\u96c6\u5408\u4fe1\u606f', '\u8f93\u5165')
nc.NODE_SEARCH_ENTRIES[:] = [points, bounds, replacement]
assert 'random' not in search('shili')
assert nc.SEARCH_PINYIN_INDEX is not index
assert 'collection' in search('jihe')
nc._clear_search_caches()
assert nc.SEARCH_PINYIN_INDEX is None

geometry = entry('geometry', 'Join Geometry', '\u5408\u5e76\u51e0\u4f55\u4f53', '\u51e0\u4f55')
duplicate = entry('other-library', 'Collection Info', '\u96c6\u5408\u4fe1\u606f', '\u8f93\u5165')
nc.NODE_SEARCH_ENTRIES[:] = [geometry, replacement, duplicate]
found = search('jihe')
assert set(found) == {'geometry', 'collection', 'other-library'}
assert search('jihe', ['other-library'])[0] == 'other-library'

nc.NODE_SEARCH_ENTRIES[:] = [entry('english', 'Ping Pong', '\u4e52\u4e53', '\u8fd0\u7b97'),
                           entry('chinese', 'Screen Size', '\u5c4f\u5e55\u5927\u5c0f', '\u8f93\u5165')]
assert search('ping')[0] == 'english'
assert search('p i n g') != search('\u5c4f'), 'Letters are not complete syllables'
print('PINYIN_INTEGRATION_OK', bpy.app.version_string, flush=True)
