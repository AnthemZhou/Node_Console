"""Compare Chinese/pinyin and legacy English ordering in isolated Blender."""
import importlib.util
import json
import os
from pathlib import Path
import re
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace
from zipfile import ZipFile

import bpy

ROOT = Path(__file__).resolve().parents[1]


def load(name, root, settings):
    spec = importlib.util.spec_from_file_location(name, root / '__init__.py', submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module._settings_path = lambda: settings
    module._preferences = lambda: None
    return module


def ids(entries):
    return [entry.identifier for entry in entries]


def main():
    config = Path(os.environ['BLENDER_USER_CONFIG'])
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == config.resolve()
    bpy.context.preferences.use_preferences_save = False
    fallback = 'fallback' in sys.argv
    report = dict(version=bpy.app.version_string, baseline='1.5.1', fallback=fallback, trees={}, failures=[])
    with tempfile.TemporaryDirectory(prefix='nc-pinyin-baseline-') as directory:
        baseline = Path(directory)
        with ZipFile(ROOT / 'Node_Console_1.5.1.zip') as archive:
            archive.extractall(baseline)
        old = load('NCPinyinBaseline', baseline / 'Node_Console', config / 'old.json')
        new = load('NCPinyinCurrent', ROOT, config / 'new.json')
        if fallback:
            old._system_pinyin = new._system_pinyin = lambda text: ''
        old._refresh_asset_index()
        new._refresh_asset_index()
        for tree_type in ('GeometryNodeTree', 'ShaderNodeTree', 'CompositorNodeTree'):
            tree = bpy.data.node_groups.new('Pinyin comparison', tree_type)
            context = SimpleNamespace(space_data=SimpleNamespace(edit_tree=tree, tree_type=tree_type,
                shader_type='OBJECT', id_from=bpy.context.object), engine='BLENDER_EEVEE')
            try:
                old._rebuild_search_entries(context)
                new._rebuild_search_entries(context)
                assert ids(old.NODE_SEARCH_ENTRIES) == ids(new.NODE_SEARCH_ENTRIES)
                started = time.perf_counter()
                new._search_entries('shili', set())
                info = dict(first_pinyin_ms=(time.perf_counter() - started) * 1000,
                            pairs=0, before_exact=0, after_exact=0, after_top10=0,
                            unambiguous=0, english_priority=0, alternate_readings=0, spaced=0, favorites=0,
                            english=0, chinese=0, differences=[])
                timing = {}
                for label, queries in (
                        ('english', ('noise', 'line', 'join', 'nt', 'niose', 'set position')),
                        ('pinyin', ('shili', 'shezhi', 'weizhi', 'wenli', 'zaobo', 'yanse'))):
                    for name, module in (('before', old), ('after', new)):
                        fresh, repeated = [], []
                        for _ in range(3):
                            for query in queries:
                                module.SEARCH_QUERY_CACHE.clear()
                                start = time.perf_counter()
                                module._search_entries(query, set())
                                fresh.append((time.perf_counter() - start) * 1000)
                                start = time.perf_counter()
                                module._search_entries(query, set())
                                repeated.append((time.perf_counter() - start) * 1000)
                        timing[label + '_' + name] = dict(fresh_median_ms=statistics.median(fresh),
                                                          repeated_median_ms=statistics.median(repeated))
                info['timing'] = timing
                english = {'add', 'line', 'join', 'noise', 'nt', 'niose', 'inst', 'instance',
                           'vector math', 'stringtocurves', 'set position', 'mix', 'blur', 'math'}
                chinese = set()
                for entry in old.NODE_SEARCH_ENTRIES:
                    texts = [item.text for item in entry._native_items(1)] + [entry.chinese, *entry.aliases]
                    for text in texts:
                        for match in new.pinyin_search.PHRASE.finditer(text):
                            word = match.group()
                            chinese.add(word)
                            if len(word) > 2:
                                chinese.update((word[:2].strip(), word[-2:].strip()))
                    labels = [entry.english] + [item.text for item in entry._native_items(0)]
                    for label in labels:
                        if not label.isascii():
                            label = label.replace(old.native_search.ARROW, ' ')
                        if not label.isascii():
                            continue
                        english.add(label.lower())
                        words = re.findall(r'[a-z]+', label.lower())
                        english.update(words)
                        english.update(word[:size] for word in words for size in (2, 3, 4) if len(word) >= size)
                        english.add(''.join(word[0] for word in words))
                chinese.discard('')
                english.discard('')
                for query in sorted(english):
                    expected = ids(old._search_entries(query, set()))
                    actual = ids(new._search_entries(query, set()))
                    info['english'] += 1
                    if actual != expected:
                        report['failures'].append([tree_type, 'English changed', query, expected[:5], actual[:5]])
                for query in sorted(chinese):
                    expected = ids(old._search_entries(query, set()))
                    actual = ids(new._search_entries(query, set()))
                    info['chinese'] += 1
                    if actual != expected:
                        report['failures'].append([tree_type, 'Chinese changed', query])
                    compact = new._pinyin_profile(query)[0]
                    if not compact or not compact.isalpha() or not compact.isascii():
                        continue
                    before = ids(old._search_entries(compact, set()))
                    after = ids(new._search_entries(compact, set()))
                    info['pairs'] += 1
                    info['before_exact'] += before == actual
                    info['after_exact'] += after == actual
                    info['after_top10'] += after[:10] == actual[:10]
                    native, supplemental = new._search_candidates(0)
                    english_match = new._english_query_has_priority(compact,
                        new.native_search.ranked(native, compact), new.native_search.ranked(supplemental, compact))
                    alternatives = new._pinyin_queries(compact)
                    if english_match:
                        info['english_priority'] += 1
                    elif alternatives != (query,):
                        info['alternate_readings'] += 1
                    else:
                        info['unambiguous'] += 1
                        if after[:len(actual)] != actual:
                            report['failures'].append([tree_type, 'Pinyin parity', query, compact,
                                                       actual[:10], after[:10]])
                        if actual:
                            favorites = {actual[0], actual[len(actual) // 2], actual[-1]}
                            info['favorites'] += 1
                            with_favorites = ids(new._search_entries(compact, favorites))
                            expected_favorites = ids(new._search_entries(query, favorites))
                            if with_favorites[:len(actual)] != expected_favorites:
                                report['failures'].append([tree_type, 'Pinyin favorites', query, compact])
                        boundaries = new._pinyin_profile(query)[1]
                        spaced = ' '.join(compact[start:end] for start, end in
                                          zip((0,) + boundaries[:-1], boundaries))
                        if not new._english_query_has_priority(spaced,
                                new.native_search.ranked(native, spaced),
                                new.native_search.ranked(supplemental, spaced)):
                            info['spaced'] += 1
                            if ids(new._search_entries(spaced, set())) != after:
                                report['failures'].append([tree_type, 'Pinyin spacing', query, spaced])
                    if after != actual:
                        info['differences'].append(dict(query=query, pinyin=compact, alternatives=alternatives,
                                                       english_priority=english_match,
                                                       chinese=actual[:5], actual=after[:5]))
                if tree_type == 'GeometryNodeTree':
                    zh = new._search_entries('\u5b9e\u4f8b', set())
                    py = new._search_entries('shili', set())
                    assert ids(zh) == ids(py)
                    assert any(e.english == 'Randomize Transforms' for e in py)
                    favorite = {py[5].identifier}
                    assert ids(new._search_entries('shili', favorite)) == ids(new._search_entries('\u5b9e\u4f8b', favorite))
                    for spaced in ('SHI LI', 'shi li'):
                        found = ids(new._search_entries(spaced, set()))
                        if found != ids(zh):
                            report['failures'].append([tree_type, 'Spaced pinyin', spaced,
                                                       len(zh), len(found), ids(zh)[:5], found[:5]])
                report['trees'][tree_type] = info
                print('PINYIN_PARITY', tree_type, {k: v for k, v in info.items() if k != 'differences'}, flush=True)
            finally:
                bpy.data.node_groups.remove(tree)
    output = Path(sys.argv[sys.argv.index('--') + 1])
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('FAILURES', len(report['failures']), report['failures'][:5], flush=True)
    assert not report['failures'], 'See pinyin parity report'


if __name__ == '__main__':
    main()
