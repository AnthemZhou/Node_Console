"""Match screenshot OCR paths to entry identities, retaining unresolved rows.

Only exact normalized path matches count automatically. Fuzzy suggestions are
review aids, never accepted as native ground truth without explicit review.
"""
import argparse
from collections import defaultdict
import csv
import difflib
import json
from pathlib import Path
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_search


def normalize(text):
    return ''.join(c.casefold() for c in unicodedata.normalize('NFKD', text) if c.isalnum())


def compare(native, plugin, limit=10):
    expected = plugin[:len(native)] if native else plugin[:1]
    unique = list(dict.fromkeys(native))
    complete = len(native) < limit
    return dict(
        exact=native == expected,
        first=native[:1] == plugin[:1],
        position_matches=sum(a == b for a, b in zip(native, expected)),
        overlap=len(set(native) & set(plugin[:limit])),
        missing=list(dict.fromkeys(i for i in native if i not in plugin)),
        exact_deduplicated=unique == (plugin[:len(unique)] if unique else plugin[:1]),
        native_duplicates=len(native) - len(unique),
        native_complete=complete,
        # Ten visible rows may hide further results. For a shorter list, count
        # extras too instead of silently accepting an identical prefix.
        visible_exact=native == (plugin if complete else plugin[:limit]),
        complete_exact=native == plugin if complete else None,
        extra_results=[i for i in plugin if i not in native] if complete else None,
        plugin_result_count=len(plugin),
    )


def analyze(root):
    report = json.loads((root / 'report.json').read_text())
    ocr = {s['index']: s for s in json.loads((root / 'ocr.json').read_text())}
    review = json.loads((root / 'review.json').read_text()) if (root / 'review.json').exists() else {}
    results = []
    for sample in report['samples']:
        language = int(sample['language'] == 'zh_HANS')
        catalog = {e['id']: e for e in report['catalogs'][sample['context']]}
        path_map = defaultdict(set)
        for entry in catalog.values():
            for path in entry['paths'][language]:
                path_map[normalize(path)].add(entry['id'])
                if entry['kind'] == 'ASSET' and native_search.ARROW in path:
                    # The native asset menu omits its root catalog. Identity
                    # matching only; do not change the plugin's ranking paths.
                    path_map[normalize(path.split(native_search.ARROW, 1)[1])].add(entry['id'])
        for path, identity in review.get('path_aliases', {}).items():
            path_map[normalize(path)].add(identity)
        slots = defaultdict(list)
        for line in ocr[sample['index']]['lines']:
            x, y, width, height = line['box']
            center = (1 - y - height / 2) * 650
            slot = round((center - 156) / 40)
            if 0 <= slot < 10 and abs(center - (156 + slot * 40)) < 14 and x < 0.83:
                slots[slot].append((x, line['text']))
        for slot, count in enumerate(ocr[sample['index']].get('ink', [])):
            if count > 40:
                slots[slot]  # Preserve visible rows OCR failed to read.
        rows = []
        empty = False
        for slot in range(max(slots, default=-1) + 1):
            text = ' '.join(t for _, t in sorted(slots[slot]))
            norm = normalize(text)
            if norm in {'noresultsfound', '未找到结果', '没有找到结果'}:
                empty = True
                break
            corrected = review.get('ocr_corrections', {}).get(norm, norm)
            matches = sorted(path_map.get(normalize(corrected), ()))
            row = dict(text=text, matches=matches)
            if corrected != norm:
                row['reviewed_text'] = corrected
            if len(matches) != 1:
                closest = difflib.get_close_matches(norm, path_map, n=3, cutoff=0.7)
                row['suggestions'] = [{"path": p, "ids": sorted(path_map[p]),
                                        "ratio": difflib.SequenceMatcher(None, norm, p).ratio()} for p in closest]
            rows.append(row)
        manual = review.get(str(sample['index']), {})
        if 'native' in manual:
            native = manual['native']
            resolved = True
        else:
            resolved = (empty or bool(rows)) and all(len(r['matches']) == 1 for r in rows)
            native = [r['matches'][0] if len(r['matches']) == 1 else None for r in rows]
        item = {k: sample[k] for k in ('index', 'tree', 'language', 'query', 'group', 'context')}
        item.update(resolved=resolved, rows=rows, native=native, plugin=sample['plugin'][:10])
        if manual:
            item['review'] = manual
        if resolved:
            item.update(compare(native, sample['plugin']))
            expected = sample['plugin'][:len(native)] if native else sample['plugin'][:1]
            if not item['exact']:
                query_words = native_search.words(sample['query'])[0]
                def keys(identity):
                    entry = catalog.get(identity)
                    if entry is None:
                        return []
                    scored = []
                    for path, weight in zip(entry['paths'][language], entry['weights'][language]):
                        candidate = native_search.Item(path, weight)
                        score = native_search.score(query_words, candidate)
                        if score is not None:
                            scored.append([score, weight, candidate.main_length, candidate.total_length])
                    return sorted(scored, key=lambda k: (-k[0], -k[1], k[2], k[3]))
                item['differences'] = [dict(position=i+1, native=a, plugin=b,
                                            native_keys=keys(a), plugin_keys=keys(b))
                                       for i, (a, b) in enumerate(zip(native, expected)) if a != b]
                item['same_keys'] = bool(item['differences']) and all(
                    d['native_keys'] and d['plugin_keys'] and d['native_keys'][0] == d['plugin_keys'][0]
                    for d in item['differences'])
        results.append(item)
    summary = {}
    for group in ['baseline', 'context', 'pinyin', 'cross_language']:
        group_cases = [s for s in results if s['group'] == group]
        resolved = [s for s in group_cases if s['resolved']]
        summary[group] = dict(total=len(group_cases), resolved=len(resolved),
            first=sum(s['first'] for s in resolved), exact=sum(s['exact'] for s in resolved),
            visible_exact=sum(s['visible_exact'] for s in resolved),
            native_complete=sum(s['native_complete'] for s in resolved),
            complete_exact=sum(s['complete_exact'] is True for s in resolved),
            extra_cases=sum(bool(s['extra_results']) for s in resolved),
            exact_deduplicated=sum(s['exact_deduplicated'] for s in resolved),
            positions=sum(len(s['native']) for s in resolved),
            position_matches=sum(s['position_matches'] for s in resolved),
            same_keys=sum(s.get('same_keys', False) for s in resolved),
            missing_cases=sum(bool(s['missing']) for s in resolved))
    output = dict(version=report['version'], build=report['build'], summary=summary, cases=results)
    (root / 'analysis.json').write_text(json.dumps(output, ensure_ascii=False, indent=2))
    fields = ('index', 'group', 'context', 'language', 'query', 'resolved', 'first',
              'visible_exact', 'exact', 'native_complete', 'complete_exact',
              'position_matches', 'plugin_result_count', 'native_duplicates')
    with (root / 'cases.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=(*fields, 'native_count', 'missing', 'extra_results'))
        writer.writeheader()
        for item in results:
            row = {key: item.get(key) for key in fields}
            row.update(native_count=len(item['native']),
                       missing=json.dumps(item.get('missing'), ensure_ascii=False),
                       extra_results=json.dumps(item.get('extra_results'), ensure_ascii=False))
            writer.writerow(row)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('UNRESOLVED', [(s['index'], s['query']) for s in results if not s['resolved']])
    print('DIFFERENT', [(s['index'], s['query'], s['first'], s.get('same_keys'))
                         for s in results if s['resolved'] and not s['exact']])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    analyze(parser.parse_args().directory)
