"""Resolve complete pinyin to Chinese text already present in the node index."""
from itertools import product
import re

HAN = r'[\u3400-\u9fff]'
PHRASE = re.compile(HAN + r'+(?:\s+' + HAN + r'+)*')
QUERY = re.compile(r'[a-z]+(?: +[a-z]+)*')
MAX_ALTERNATIVES = 16


class QueryIndex:
    def __init__(self, texts, profiles):
        self.phrases = []
        phrases = {match.group() for text in texts for match in PHRASE.finditer(text)}
        for text in sorted(phrases):
            positions = tuple(match.start() for match in re.finditer(HAN, text))
            for compact, boundaries, _initials, _search in profiles(text):
                # Only a one-syllable-per-character reading can be mapped back
                # without guessing, including context-sensitive pronunciations.
                if not compact or len(boundaries) != len(positions):
                    continue
                starts = {offset: index for index, offset in enumerate((0,) + boundaries[:-1])}
                ends = {offset: index for index, offset in enumerate(boundaries)}
                self.phrases.append((text, compact, starts, ends, positions))

    def _resolve_compact(self, query):
        found = set()
        for text, compact, starts, ends, positions in self.phrases:
            offset = compact.find(query)
            while offset >= 0:
                end = offset + len(query)
                if offset in starts and end in ends:
                    found.add(text[positions[starts[offset]]:positions[ends[end]] + 1])
                    if len(found) > MAX_ALTERNATIVES:
                        return ()
                offset = compact.find(query, offset + 1)
        return tuple(sorted(found))

    def resolve(self, query):
        query = ' '.join(query.lower().split())
        if len(query.replace(' ', '')) < 2 or not QUERY.fullmatch(query):
            return ()
        direct = self._resolve_compact(query.replace(' ', ''))
        if direct or ' ' not in query:
            return direct
        choices = []
        count = 1
        for token in query.split():
            translated = self._resolve_compact(token)
            count *= len(translated)
            if not translated or count > MAX_ALTERNATIVES:
                return ()
            choices.append(translated)
        return tuple(sorted({' '.join(words) for words in product(*choices)}))
