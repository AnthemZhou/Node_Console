"""Locale-specific search keys, never display translations or IME conversion.

Unicode normalization and Hangul decomposition follow UAX #15 / chapter 18.
Kana folding does not infer kanji readings. Spanish n/enye stay distinct.
"""
from functools import lru_cache
import re
import unicodedata

_SPANISH = str.maketrans('áéíóúü', 'aeiouu')
_KANA = str.maketrans({code: code - 0x60 for code in
                      (*range(0x30A1, 0x30F7), 0x30FD, 0x30FE)})


@lru_cache(maxsize=8192)
def search_key(text, language):
    if language == 'zh_HANS':
        return text
    text = unicodedata.normalize('NFKC', text).casefold()
    if language == 'ja_JP':
        return text.translate(_KANA)
    if language == 'ru_RU':
        return text.replace('ё', 'е')
    if language == 'es':
        return text.translate(_SPANISH)
    return text


def initials(text):
    result = []
    for char in text:
        value = ord(char)
        if 0xAC00 <= value <= 0xD7A3:
            result.append(chr(0x1100 + (value - 0xAC00) // 588))
        else:
            result.append(char)
    return ''.join(result)


def profile(text, language):
    words = tuple(x for x in re.split(r'[^\w]+', search_key(text, language)) if x)
    compact = ''.join(words)
    forms = tuple(dict.fromkeys((compact, *words)))
    if language == 'ko_KR':
        return forms, tuple(initials(x) for x in forms), tuple(unicodedata.normalize('NFD', x) for x in forms)
    return forms, (), ()


@lru_cache(maxsize=512)
def query_profile(query, language):
    compact = ''.join(re.findall(r'\w+', search_key(query, language)))
    consonants = language == 'ko_KR' and len(compact) >= 2 and all(0x1100 <= ord(c) <= 0x1112 for c in compact)
    decomposed = unicodedata.normalize('NFD', compact) if language == 'ko_KR' else ''
    return compact, consonants, decomposed


def extension_level(prepared, query, language):
    compact, consonants, decomposed = query_profile(query, language)
    if not compact:
        return 0
    forms, initials_forms, decomposed_forms = prepared
    if consonants:
        return 5 if compact in initials_forms else 4 if any(x.startswith(compact) for x in initials_forms) else 0
    # Local-script space-free prefixes and an unfinished Korean syllable are
    # explicit matches, not fuzzy edit-distance accidents. Keep Latin initials
    # and spelling to the existing native ranker.
    if not compact.isascii():
        if compact in forms:
            return 5
        if len(compact) >= 2 and any(x.startswith(compact) for x in forms):
            return 4
        if language == 'ko_KR' and len(decomposed) >= 2 and any(x.startswith(decomposed) for x in decomposed_forms):
            return 4
    return 0


def clear():
    search_key.cache_clear()
    query_profile.cache_clear()
