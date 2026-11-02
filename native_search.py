"""Blender-compatible menu search, independent of bpy and display language.

SPDX-License-Identifier: GPL-2.0-or-later
Upstream: Blender Authors, source/blender/blenlib/intern/string_search.cc.
Equal-length C++ unstable-sort ties are not guaranteed to match Python's stable
sort. Favorites and transliteration belong in the caller, not in this module.
"""
from dataclasses import dataclass
import re
from functools import lru_cache

ARROW = '\u25b8'
ASCII_LOWER = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')


@lru_cache(maxsize=4096)
def words(text):
    result, groups = [], []
    for group, section in enumerate(text.translate(ASCII_LOWER).split(ARROW)):
        parts = [x for x in re.split(r'[ /_\-]+', section) if x]
        result.extend(parts)
        groups.extend([group] * len(parts))
    return tuple(result), tuple(groups)


def distance(a, b):
    previous2 = [0] * (len(b) + 1)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        row = [i + 1] + [0] * len(b)
        for j, cb in enumerate(b):
            value = min(previous[j+1]+1, row[j]+1, previous[j]+(ca != cb))
            if i and j and ca == b[j-1] and a[i-1] == cb:
                value = min(value, previous2[j-1]+1)
            row[j+1] = value
        previous2, previous = previous, row
    return previous[-1]


@lru_cache(maxsize=8192)
def fuzzy(query, full):
    if query in full:
        return 0
    if len(query) == 1:
        return -1
    errors = len(query) // 8 + 1
    if len(query) - len(full) > errors:
        return -1
    size = min(len(query) + errors, len(full))
    acceptable = errors + max(size - len(query), 0)
    start = 0
    while True:
        delta = 0
        if full[start:start+1] in query[:2] and full[start:start+1]:
            delta = distance(query, full[start:start+size])
            if delta <= acceptable:
                return delta
        if start + size == len(full):
            return -1
        start += min(max(1, delta // 2), len(full) - start - size)


@dataclass
class Item:
    text: str
    weight: float = 0
    recent: int = -1
    data: object = None

    def __post_init__(self):
        self.words, self.groups = words(self.text)
        self.main = self.groups[-1] if self.groups else 0
        self.main_length = sum(len(w.encode()) for w, g in zip(self.words, self.groups) if g == self.main)
        self.total_length = len(self.text.encode())


def initials(query, item, used, start=0):
    if start >= len(item.words):
        return None
    matched, wi, ci, first = [], start, 0, -1
    for char in query:
        while True:
            if wi >= len(item.words):
                return initials(query, item, used, first+1) if first >= 0 else None
            if used[wi] != -1:
                wi += 1
                continue
            word = item.words[wi]
            if ci < len(word):
                wc = word[ci]
                ci += 1
                if char == wc:
                    matched.append(wi)
                    if first < 0:
                        first = wi
                    break
            wi += 1
            ci = 0
    later = initials(query, item, used, first+1)
    main_count = lambda indices: sum(item.groups[i] == item.main for i in indices)
    if later is not None and main_count(later) > main_count(matched):
        return later
    return matched


def score(query_words, item):
    used = [-1] * len(item.words)
    result = 500 if 'eprecated' in item.text else 1000
    for qi, query in enumerate(query_words):
        shortest = any(w.startswith(query) for w in query_words[qi+1:])
        best, best_size, best_main = -1, 2**31, False
        for i, word in enumerate(item.words):
            if used[i] != -1 or not word.startswith(query):
                continue
            if (len(word.encode()) < best_size) if shortest else not best_main:
                best, best_size, best_main = i, len(word.encode()), item.groups[i] == item.main
        if best >= 0:
            result += 10 if best_main else 9
            used[best] = qi
            continue
        found = initials(query, item, used)
        if found is not None:
            result += 4 if all(item.groups[i] == item.main for i in found) else 3
            for i in found:
                used[i] = qi
            continue
        for i, word in enumerate(item.words):
            if used[i] != -1:
                continue
            errors = fuzzy(query, word)
            if errors >= 0:
                result += 3 - errors
                used[i] = qi
                break
        else:
            return None
    indices = [i for i in used if i != -1]
    return result - sum(a > b for a, b in zip(indices, indices[1:]))


def ranked(items, query):
    groups = {}
    query_words, _ = words(query)
    for item in items:
        value = score(query_words, item)
        if value is not None:
            groups.setdefault(value, []).append(item)
    result = []
    for i, value in enumerate(sorted(groups, reverse=True)):
        group = groups[value]
        if i == 0:
            if query:
                group.sort(key=lambda item: (item.main_length, item.total_length))
                group.sort(key=lambda item: -item.weight)
            if len(query.encode()) <= 1:
                group.sort(key=lambda item: -item.recent)
        result.extend((value, item) for item in group)
    return result


def search(items, query):
    return [item for _score, item in ranked(items, query)]


def clear():
    words.cache_clear()
    fuzzy.cache_clear()


def self_test():
    # The 18 numeric cases and word extraction fixture from upstream tests.
    cases = [('test','test',0),('hello','ell',2),('hello','hel',2),
             ('ell','hello',2),('hell','hello',1),('hello','hallo',1),
             ('test','',4),('','hello',5),('Test','test',1),('ab','ba',1),
             ('what','waht',1),('what','ahwt',2)]
    for a, b, expected in cases:
        assert distance(a, b) == expected, (a, b)
    for a, b, expected in [('a','b',-1),('','abc',0),('hello','hallo',1),
                           ('hap','hello',-1),('armature',ARROW+'restore',-1)]:
        assert fuzzy(a,b) == expected, (a,b)
    assert fuzzy('bluir','blur') == fuzzy('blur','bluir')
    assert words('hello world'+ARROW+'test   another test'+ARROW+' 3') == (
        ('hello','world','test','another','test','3'), (0,0,1,1,1,2))
    item = Item('Add '+ARROW+' Geometry '+ARROW+' Join Geometry')
    assert score(['join'],item) == 1010
    assert score(['jg'],item) == 1004
    assert score(['geometry','join'],item) == 1019
    assert score(['jion'],item) == 1002
    weighted = [Item('Add '+ARROW+' Mesh Join', 0), Item(item.text, 1)]
    assert search(weighted,'join')[0].weight == 1
    return {'upstream_fixtures': 19, 'additional_rule_checks': 5}


if __name__ == '__main__':
    print(self_test())
