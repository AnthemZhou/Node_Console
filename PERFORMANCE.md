# Node Console Performance

## 1.5.0 Multilingual Search

Release validation on macOS arm64, isolated Blender
5.2.2 LTS (`d13f752e3b9c`) and 5.1.2 (`ec6e62d40fa9`). No personal Blender
preferences, installed add-ons or project files are modified by these tests.

### Translation and Matching Scope

- Use the installed Blender MO files, not a network translation service. Select
  one of Chinese, Japanese, Korean, Russian and Spanish alongside English.
  Blender's locale IDs and catalog directories differ: `ja_JP`/`ja`,
  `ko_KR`/`ko`, `ru_RU`/`ru`, plus `zh_HANS` and `es`.
- Resolve RNA and enum/menu contexts, then the default context, then English.
  This follows Blender's [translation-context design](https://developer.blender.org/docs/features/interface/internationalization/).
  Chinese editorial aliases remain explicitly separate. Do not change the
  user's Blender interface language to obtain translations.
- New locales normalize Unicode case, full/half-width forms and composed
  characters. Japanese folds katakana to hiragana for matching, not display;
  Korean supports initial consonants, omitted spaces and partial syllables;
  Russian folds `ё` to `е`, Spanish folds accents but preserves `ñ`. Retain
  Japanese voicing and Russian hard/soft signs. Unicode normalization and
  Hangul decomposition follow [UAX #15](https://unicode.org/reports/tr15/).
  No speculative kanji readings or romanization dictionary is added. Keep
  the original Chinese ranking path unchanged.
- New locales use the existing scoring formula with separate English/local
  candidate orders. Spanish chooses the higher top score, favoring English
  on ties. Source text retains official UTF-8 sorting and lengths, independently
  of matching keys. This still does not promise an identical monolingual list:
  additional case-insensitive, bilingual and abbreviation matches are intentional.
- Load only the selected catalog; persist per-language indexes and retain the
  bounded recent-query cache. Existing cache schema is bumped to 7. Entry IDs,
  favorites, usage and settings do not depend on translated text. Japanese
  kanji are not sent through Chinese pinyin preprocessing.

### Validation

`tools/test_multilingual.py` independently reads the installed gettext catalogs
and exercises the registered preferences, every indexed built-in entry,
all five locales and all three editors. Across the two Blender versions:

- 43,311 search assertions: English and localized names, operation variants,
  uppercase, whitespace, decomposed accents/Hangul and full-width input.
- 10,215 node creations using the add-on's actual creation entry point. These
  are repeated node/variant creations across locales, not new node counts.
- 14,954 additional typing-variant reachability checks over official translated
  entries, 60 live-favorite checks and 120 snippet-name/ordering checks. These
  verify membership, not top-one ranking for every ambiguous abbreviation.
- 16 representative everyday queries improve from 12 to 16 passing top-five
  checks. Across 144 English top-five comparisons, all original prefixes remain
  intact (143 identical lists; the short Spanish shader `position` result grows
  with additional lower-ranked translated matches).
- Stable identifiers across languages, cache round trips, English fallback,
  real translated-name coverage, preference persistence and unchanged Blender
  UI language. User-data sentinels survive switching languages and rebuilding.
- Against the published 1.4.7 ZIP, 23,110 complete ordered-list comparisons
  remain identical in default Chinese mode, including live favorite boosts.
- The existing 194 native-search probes retain 178 comparable cases, 177
  first-result/empty agreements, 159 exact visible lists, 1,131/1,193 matching
  positions and zero missing native-result cases. These remain the original
  English/Chinese oracle, not evidence of Japanese/Korean/Russian/Spanish parity.
- A separate set of 52 actual `NODE_MT_add` popup captures in the four new
  languages covers all three editors in Blender 5.2.2. Exact OCR path resolution
  (no fuzzy oracle substitution) gives 52/52 matching first results, 48/52
  matching visible lists, 193/198 matching positions and no missing captured
  results. Four ten-row menus may continue below the captured region. Of the
  other 48 complete native lists, 44 match completely; four include additional
  valid case-insensitive/bilingual matches in Node Console. These differences
  are retained rather than hiding useful nodes. The portable fixture is
  `tools/fixtures/native_search_multilingual_5_2_2.json`, not a claim of
  universal native parity or language fluency.

Selected-language translation coverage in Blender 5.2.2, counting unparameterized
RNA-name entries whose displayed name differs from English (not a percentage
of all catalog strings, and not necessarily a missing translation when equal):

| Language | Geometry | Shader | Compositor |
| --- | ---: | ---: | ---: |
| Chinese | 359 | 118 | 167 |
| Japanese | 359 | 118 | 166 |
| Korean | 320 | 117 | 160 |
| Russian | 359 | 118 | 167 |
| Spanish | 355 | 113 | 163 |

The GPU input-preview harness accepts `--language ja_JP`, `ko_KR`, `ru_RU`
or `es` after the isolated runner's `--` separator. It verifies preedit,
document commit, cancellation, clear and repeated opening, observing the real
draw callback and reading the committed panel framebuffer. These are synthetic
bridge events, **not physical system-IME or candidate-window validation**.
The second pass checks Noise Texture is reachable during preedit as well as
after commit in all four languages, across three open/close cycles each
(60 draw/input observations total).

Existing Chinese Mac/Windows acceptance is unchanged. New language-specific
system IMEs, Intel Mac, Windows/Linux hardware and keyboard-layout behavior are
not certified by these tests. New-language result paths can be longer, so their
category label is capped to leave space for the node name. Timing samples from
correctness runs are diagnostic only, not a new performance-speedup claim.

`tools/benchmark_language_experience.py` compares the pre-polish 1.5.0 ZIP with
this pass over four locales and three editors. In one diagnostic 5.2.2 run,
uncached-query medians are 0.72-3.99 ms and repeated-query medians 0.009-0.026 ms;
first-query candidate preparation is 5.85-26.81 ms. Spanish still needs both
Latin-script indexes and does not share the same cost reduction as the three
distinct-script languages. These are Python search timings, not total popup,
physical typing or OS candidate-window latency; no new platform-wide speedup
claim is made.

Reproduce through `tools/run_isolated_blender.py` using
`tools/test_multilingual.py`, `tools/test_search_cache.py`,
`tools/test_user_data.py`, `tools/test_preferences_ui.py`,
`tools/test_expanded_native_search.py`, and
`tools/benchmark_search_latency.py Node_Console_1.4.7.zip <output.json>`.
For the additional native oracle, run `tools/test_expanded_native_search.py
<output.json> --fixture tools/fixtures/native_search_multilingual_5_2_2.json
--multilingual` through the isolated runner (put options after its `--`).
`tools/audit_language_experience.py <output.json> --verify` checks the everyday
queries and English-order invariants. `tools/test_search_language.py` covers
negative normalization cases and bounded caches without Blender.
Detailed reports and screenshots stay under ignored `build/`.

## 1.4.7 Open and Input Latency

Baseline: published 1.4.6 ZIP. macOS arm64, isolated Blender 5.2.2 LTS
(`d13f752e3b9c`); no personal preferences or project data are used.
No native scoring formula, weights, keymaps, IME polling or focus code changes.

### Index Preparation

Three fresh processes per version, alternating execution order. Cold values are
medians of the three full index builds. Disk and memory values are medians of
the three runs' existing three/five-sample medians. This batch excludes asset
scanning, native IME activation and GPU drawing, and is not cold-filesystem or
whole-popup latency. Runtime capability probes are still performed.

| Editor | No persisted index, before / after | Persisted index, before / after | Memory index, before / after |
| --- | ---: | ---: | ---: |
| Geometry | 322.48 / 203.68 ms | 30.15 / 22.32 ms | 4.06 / 3.49 ms |
| Shader | 171.89 / 101.28 ms | 20.86 / 16.01 ms | 4.23 / 3.14 ms |
| Compositor | 159.60 / 103.88 ms | 21.03 / 15.89 ms | 4.22 / 2.91 ms |

The largest cold-path reduction comes from no longer transliterating the old
full-text search field for every built-in entry and bilingual display label.
Current native matching retains Chinese, pinyin and initials profiles; snippet
full-text indexing is unchanged. Existing persisted legacy metadata is readable.
An internal read-only JSON converter constructs detached entries without a deep
copy of all raw records; mutable socket settings are copied. Public JSON reads
and atomic writes retain their isolation guarantees. Runtime signatures are
computed once per rebuild rather than twice.

### Query Processing

The three-editor benchmark includes built-in assets. It separates first input,
uncached matching and immediately repeated input, instead of presenting a cache
hit as the speed of every keystroke. Uncached-query medians cover five rounds of
25 strings with the new result cache explicitly cleared before each query;
existing word/fuzzy caches may be warm. First-input values are individual samples
after index preparation, not statistically stable end-to-end typing estimates.

| Editor | First `设置`, before / after | Uncached query, before / after | Immediate repeat, before / after |
| --- | ---: | ---: | ---: |
| Geometry | 19.45 / 16.21 ms | 2.33 / 2.03 ms | 2.32 / 0.023 ms |
| Shader | 5.98 / 4.91 ms | 1.05 / 0.94 ms | 0.97 / 0.011 ms |
| Compositor | 7.42 / 4.17 ms | 1.15 / 1.06 ms | 1.09 / 0.012 ms |

Candidates are prepared only for the requested query language and sorted once
per active entry snapshot. Alias/pinyin preprocessing no longer constructs
retired category/whole-word matching fields. Up to 32 exact query strings retain
the unboosted order and strong-match IDs; every search applies current favorites
and returns a fresh list. Entry replacement, reorder, editor/context changes and
explicit cache reset invalidate matches. No query cache is written to disk.

The complete result lists match 1.4.6 across 12,158 comparisons on 5.2.2,
including generated English/Chinese names, pinyin, initials, prefixes, whitespace,
case, typos, misses and changed favorites. The 194 independently captured native
queries retain 177/178 first-result/empty outcomes, 159/178 strict visible lists,
1,131/1,193 matching captured positions and zero captured-result omissions.

Blender 5.1.2 (`ec6e62d40fa9`) adds 10,952 matching full-list comparisons, for
23,110 total. Its uncached-query medians are 2.18 -> 1.83 ms (Geometry),
1.09 -> 0.92 ms (Shader), and 0.98 -> 0.85 ms (Compositor). Its Shader first-input
sample is slightly slower (5.26 -> 5.47 ms), so first-keystroke gains are not
claimed universal. Both builds pass cache invalidation and node creation tests;
135 pure-Python tests and isolated 5.2.2 user-data/hot-reload tests also pass.

Real GPU popup tests pass three open/close cycles and 15 synthetic
preedit/commit/cancel/clear transitions in each Blender version. The observer
checks that the expected query text is actually submitted for drawing, not only
that Python state changed. Timings stop at draw-callback completion, not display
presentation. Individual 5.2.2 first-preedit runs vary roughly 34-84 ms after
the changes; timer scheduling and one-off initialization still matter. These
runs support functional regression coverage, not a reliable whole-UI speedup
percentage. No physical IME candidate latency or Windows/Linux performance was
measured, and no user's running Blender installation or preferences were changed.

Reproduce through `tools/run_isolated_blender.py` with `tools/benchmark_open.py`,
`tools/benchmark_search_latency.py Node_Console_1.4.6.zip report.json`,
`tools/test_search_cache.py`, and `tools/test_expanded_native_search.py`.
Local raw reports stay in ignored `build/performance-*.json` and UI captures in
`build/performance-next-ui-*/`, outside Git and install packages.

## 1.4.6 Native Search Alignment

Date: 2026-11-02. Actual native `NODE_MT_add` search screenshots on macOS arm64,
Blender 5.2.2 LTS (`d13f752e3b9c`), in an isolated factory profile with bundled
assets, pinned node-group editors, and no favorites or search history.

The fixed sample has 194 queries: 162 Geometry/Shader/Compositor baseline cases,
16 World/Cycles context cases, and 16 separate pinyin/cross-language probes.
OCR rows were matched by exact paths with explicit review of ambiguous text;
native results were not generated by our ranking algorithm.

| Metric across 178 directly comparable queries | 1.4.5 | 1.4.6 |
| --- | ---: | ---: |
| First result / empty outcome | 168/178 (94.4%) | 177/178 (99.4%) |
| Strict visible order | 130/178 (73.0%) | 159/178 (89.3%) |
| Same entry at same captured position | 976/1193 (81.8%) | 1131/1193 (94.8%) |
| Cases missing a captured native result | 8 | 0 |

Strict order covers up to ten native rows and rejects extra plugin results when
the native list is shorter. It is not a full-tail or all-query parity claim.
Pinyin/cross-language probes do not contribute to these percentages. The one
first-result difference is a tied Compositor `s` query; other differences include
native duplicate rows, alias matches and supplemental registered nodes.

The fixes change menu collection, RNA identity matching, missing variants,
asset paths and menu-context filtering, not the core scoring formula or keyword
weights. Index schema 5 rebuilds cached metadata without resetting user data.
Creation, cache and context tests also pass on Blender 5.1.2; no new Windows
native-UI parity run was performed. The sample is targeted, not a statistical
estimate of every possible query, owner type, asset library or Blender build.

Reviewed native rows are preserved in
`tools/fixtures/native_search_expanded_5_2_2.json`, without personal paths or
screenshots. Reproduce with `tools/test_expanded_native_search.py` and
`tools/test_native_menu_gaps.py` through `tools/run_isolated_blender.py`.
Capture/OCR tools remain available for future audits. Raw captures and detailed
per-version reports stay local under ignored `build/` and `VALIDATION_*.md`.

## 1.4.5 Native Search Ranking

### Chinese Input Follow-Up

The later 1.4.5 input pass removes unused legacy match fields from the hot path.
In the same isolated 5.2.2 environment, ten warmed searches for `设置` have
median core times of 7.93 -> 1.70 ms (Geometry), 3.72 -> 0.78 ms (Shader), and
3.72 -> 0.92 ms (Compositor). Cold Geometry matching is 26.79 -> 21.11 ms.
All complete result lists for the 18-query, three-editor profiling batch remain
identical before/after this optimization. Generated per-entry names, aliases,
pinyin and initials also retain their legacy extension-match levels.

A separate real-UI test exposed a larger one-off cost in `blf.dimensions`:
the first CJK result frame spent 153-187 ms drawing, mostly preparing the font.
The add-on now schedules a single CJK width measurement 0.5 seconds after
enabling, defers it during an active console, skips background Blender, and
removes the timer on disable. It uses Blender's existing font; it neither
replaces the font nor changes preferences. This moves roughly 170 ms of
one-time initialization out of typing, rather than claiming to eliminate it.
Typing immediately after enabling, before preparation runs, can still be cold.

Measured synthetic IME enqueue -> draw-callback completion on 5.2.2:
first preedit 215.82 -> 39.26 ms; committed `设置` about 19.64 ms after the
preedit. The final 5.1.2 run records 46.76 ms and 12.70 ms respectively.
Three open/close cycles with five preedit/commit/cancel/clear transitions each
passed in both versions. These are real popup drawing tests with synthetic
bridge events, not physical keyboard/IME candidate latency or display scanout.
Windows system-IME responsiveness was not measured in this round.

Composition now previews results without committing text. Confirmation applies
Chinese matching immediately; cancellation restores the committed query or
shortcut list. Native Enter/Escape ownership, idle redraw gating and the 20 ms
bridge polling interval are unchanged.

Reproduce with `tools/profile_search_input.py` and, with `--ui`,
`tools/capture_input_preview.py` through the isolated runner. Local screenshots
and raw timings are under `build/native-search-1.4.5/input-preview-final/`.

### Initial Ranking Pass

Date: 2026-11-02. macOS arm64, isolated Blender 5.2.2 LTS (`d13f752e3b9c`).
Baseline: published 1.4.4 ZIP. Both versions index the same built-in assets and
temporary local groups; no personal settings or project data are used.

| Editor | 1.4.4 / 1.4.5 search median | 1.4.5 warm index preparation | 1.4.5 disk-cache preparation |
| --- | ---: | ---: | ---: |
| Geometry | 9.61 / 8.69 ms | 4.10 ms | 29.46 ms |
| Shader | 4.61 / 4.09 ms | 3.90 ms | 19.98 ms |
| Compositor | 4.66 / 4.42 ms | 4.04 ms | 20.65 ms |

Search medians cover three warmed rounds of ten English, Chinese, pinyin,
abbreviation and typo queries. This is primarily a relevance update, not a
claim of a major speedup. Ranking intentionally changes; upgrade checks instead
require persistent identities and stored user data to remain identical.
The 1,155 tested identities include variants, assets and temporary local groups,
not 1,155 unique Blender node types.

Index measurements use a separate test without scanning built-in assets.
Five warm calls and three fresh-module disk-cache calls are measured. A fully
invalidated index takes approximately 310 / 164 / 155 ms in the three editors.
Menu-path metadata is built only on this cold path, persisted with schema 4,
and reused on later opens. These are core Python timings, not GPU rendering,
IME startup or input-to-display latency. Windows/Linux timings were not measured.

Reproduce with `tools/test_search_upgrade.py -- Node_Console_1.4.4.zip report.json`
and `tools/benchmark_open.py -- report.json` through `tools/run_isolated_blender.py`.
Native UI comparisons are separately covered by `tools/capture_native_search.py`
and `tools/test_native_menu_search.py`; pure matching tests include upstream
Blender vectors. Raw reports and screenshots stay local and outside the ZIP.

## 1.4.4 First-Open Index Preparation

Date: 2026-10-30. Baseline: published 1.4.3 ZIP (SHA256
`8418ab734cdf93ecc9e90c6e436c2adfab5f9de4902661f2083deae9ec59d389`).
Tests run in isolated macOS arm64 Blender processes with synthetic settings,
not personal preferences.

| Editor | 5.2.2 first open with disk cache, before / after | 5.1.2 before / after | 5.2.2 subsequent opens, before / after |
| --- | ---: | ---: | ---: |
| Geometry | 222.94 / 26.72 ms | 190.68 / 22.89 ms | 21.40 / 4.10 ms |
| Shader | 141.18 / 18.84 ms | 134.26 / 16.67 ms | 12.13 / 3.89 ms |
| Compositor | 139.78 / 19.34 ms | 117.06 / 16.27 ms | 12.40 / 4.07 ms |

First-open medians cover three fresh module instances with a persisted index;
subsequent medians cover five calls. These time index preparation only, not native
IME activation, GPU drawing, input-to-display latency or a cold filesystem.
First installation/cache invalidation still needs a full build: about 297 ms
for Geometry, 158 ms for Shader and 146 ms for Compositor on 5.2.2 in this run.
This one-off path is not claimed as a speedup. Index schema 3 rebuilds the old
cache once, without resetting favorites, shortcuts, usage weights or settings.

The completed index now preserves translated search text and pinyin profiles.
Matching disk snapshots skip menu parsing and translation reconstruction; bounded
memory snapshots also reuse entry objects. Keys include the Blender build,
editor, experimental switches, tree flags, RNA registrations and asset snapshot.
Display mode and settings revisions invalidate in-memory entries. Project node
groups remain live; missing asset files are still filtered, and node capability
probes are retained. Reopening no longer appends duplicate zone entries.

Reproduce with `tools/benchmark_open.py -- report.json [baseline_package_dir]`
in a factory-startup Blender process with pre-created isolated config, scripts,
datafiles and temporary directories. Tests cover disk/memory/cold parity,
Chinese/pinyin/initials, display modes, live group edits, third-party node
registration, deleted assets, incomplete caches, native node creation and colors.

## 1.4.3 Shortcut Saves

Date: 2026-10-30. Baseline: published 1.4.2 ZIP. The real Add Shortcut modal
handler runs against identical synthetic 2,677,362-byte settings files containing
multiple node-index caches. Medians below cover 15 warmed, unprofiled calls,
resetting the settings before each addition. No personal data is used in this
benchmark. The complete persisted settings match the baseline.

| Operation | Blender 5.2.2 before / after | Blender 5.1.2 before / after |
| --- | ---: | ---: |
| Add Shortcut, including save and list refresh | 191.92 / 33.62 ms | 196.18 / 34.47 ms |

The previous handler deep-copied all settings and saved the file three times.
It now copies only the changed fields, preserves unrelated cached values and
commits the shortcut list, editor scope and label once. Identical repeat additions
do not write. Atomic replacement, unreadable-file protection and external-change
checks remain in place. Failed saves do not clear the query or show an unsaved
shortcut. No deferred writes, new data files or keymap changes are introduced.

These are macOS arm64 handler timings, not GPU/input-to-display latency or Windows
measurements. Filesystem speed, index size and installed add-ons affect results.
Run `tools/benchmark_shortcut_save.py -- /tmp/nc-shortcut-performance.json` with a
factory-startup Blender process and pre-created, isolated configuration directories.
The script compares against `Node_Console_1.4.2.zip` in the repository.

## 1.3.2 User-Data Hot Paths

Date: 2026-10-18. Baseline: published 1.3.1 ZIP. These measurements use separate temporary user-data files in the same factory-startup Blender process. No personal preferences or snippet libraries are read or modified.

The synthetic library has 200 snippets, each containing a frame, 12 Math nodes and 11 links (about 5 MB JSON). Settings include three editor indexes and both versioned cache keys (about 1.3 MB on 5.2.2). Both implementations receive identical initial data. Values are medians of 15 warmed calls, or five calls resetting snippet caches for first-query timing.

| Operation | Blender 5.2.2 before / after | Blender 5.1.2 before / after |
| --- | ---: | ---: |
| Read editor favorites and shortcuts | 41.79 / 0.33 ms | 37.91 / 0.34 ms |
| Preferences content, snippets collapsed | 159.29 / 1.78 ms | 148.61 / 1.70 ms |
| Preferences content, snippets expanded | 157.34 / 3.11 ms | 148.88 / 3.13 ms |
| Subsequent snippet query | 31.98 / 0.20 ms | 32.15 / 0.21 ms |
| First snippet query after cache reset | 33.09 / 33.78 ms | 32.71 / 34.13 ms |

These are Python processing measurements, not end-to-end popup latency, disk-cold startup, or GPU/UI frame rates. Preferences uses the real draw method with a recording layout in place of native widgets. Improvements depend on library/cache size. First-query performance is approximately unchanged, slightly slower in these runs; the benefit is eliminating repeated work after loading. Reading unchanged small settings no longer parses unrelated indexes. Search and list rendering retain metadata only; full graph data is copied only for edits or creation. File contents are reloaded when path, file identity, size or nanosecond modification/change timestamps change.

Both Blender versions pass 60 snippet result/order comparisons against 1.3.1, covering English, Chinese, pinyin, initials, empty queries, misses, favorite changes and all three editor scopes. Additional checks cover external same-size edits/replacement, library switches, mutable-copy isolation, atomic-write failures, failed-save Frame restoration, stale-result insertion, collapsed Preferences, shortcut ordering, native-node creation/index coverage, package installation and package-local hot-reload/rollback. Existing search matching, category colors and keymap registration are unchanged.

32 pure-Python tests pass. The real Blender suites use 5.2.2 LTS (`d13f752e3b9c`) and 5.1.2 (`ec6e62d40fa9`) on macOS arm64. No Windows/Linux native run, manual GUI-latency measurement, power-loss durability test, or simultaneous multi-process write/merge guarantee is claimed. Atomic replacement protects against partial writes but is not a backup or a multi-writer database.

Reproduce with the published `Node_Console_1.3.1.zip` in the repository:

```sh
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/benchmark_user_data.py -- /tmp/nc-user-data-performance.json
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/test_user_data.py
python3 -m unittest tools.test_json_store tools.test_addon_updater tools.test_release_package
```

Local raw reports are under ignored `Display/Optimization_2026-10-18/`, excluded from the add-on ZIP and Git.

## 1.2.2 Search Performance

Date: 2026-10-06. Baseline: published 1.2.1 (`237708f`). This report covers the performance changes included in 1.2.2. The baseline ZIP remains unchanged.

### Changes

- Prepare immutable entry names, categories, aliases and pinyin profiles once per entry instead of on every keystroke. This data is not serialized and replacement entries get fresh caches.
- Bound normalization and word-token caches to 8,192 strings each, and query-priority cache to 256 queries. Clear them with the existing cache-reset path.
- Reuse per-query matches for the weak-pinyin fallback. Blank queries return immediately.
- Obtain runtime capabilities once per index rebuild instead of repeatedly recalculating the runtime signature for individual entries. Index rebuilds still refresh local groups, assets and preferences.
- Do not cache final search results, favorites or settings. No keymap, node identity, persistence schema or ranking changes.

### Measurements

macOS arm64, actual Blender 5.2.2 LTS (`d13f752e3b9c`), factory-startup background process. Baseline and current code run in the same process with separate temporary settings. The baseline ZIP SHA256 is `8f2f57a859bae64c59377c8a413e897054a4b709592d4bbe398e2a76f497fc0a`.

| Editor | Search median before / after | Warm index preparation before / after |
| --- | ---: | ---: |
| Geometry | 19.99 / 8.29 ms | 71.22 / 26.66 ms |
| Shader | 10.60 / 4.59 ms | 51.69 / 27.36 ms |
| Compositor | 10.56 / 4.87 ms | 58.92 / 32.97 ms |

Search timings cover 33 queries, each with and without favorites. Queries include English, Chinese, pinyin, initials, case/space variations, partial input and misses. Warm index timing is the median of three rebuilds. The benchmark indexes contain 517 / 276 / 282 entries, including variants and temporary local groups; these are not unique native-node counts.

These are core-function measurements, not end-to-end popup latency or GUI frame rates. Cold timings are recorded but not used to claim a speedup because Blender/OS initialization and run order affect them. Absolute timings vary by machine and workload.

Blender 5.1.2 also improves: search medians are 18.47 / 8.16 ms (Geometry), 10.39 / 4.68 ms (Shader), and 8.78 / 3.94 ms (Compositor). Warm rebuild medians are 67.19 / 25.54, 52.91 / 24.28, and 52.45 / 28.81 ms respectively.

### Regression Coverage

- Blender 5.2.2: 5,516 generated name/pinyin/initial/prefix queries plus 198 fixed-query/favorite cases have identical complete result order to 1.2.1 (5,714 comparisons, zero differences).
- Blender 5.1.2: 5,023 generated queries plus 198 fixed-query/favorite cases also match exactly (5,221 comparisons). Combined total: 10,935 comparisons, zero differences.
- Blender 5.2.2 and 5.1.2 (`ec6e62d40fa9`): actual search/create checks, menu and registered-type coverage, bilingual display, fallback pinyin, warm-cache identities, same-name asset isolation and preservation of settings/language pass.
- Blender 5.2.2: 1,063 native entry/variant creations and 83 asset creations retain the audited colors; zero failures.
- Both Blender versions: ten cache checks pass, covering preprocessing reuse, live favorites, serialization, changed names/aliases, empty/missed searches, bounded caches, cache reset, local group rename/removal and snippet edits/deletion.
- The released 1.2.2 ZIP passed installation, enable/disable/re-enable and three-editor index checks in isolated temporary directories on both Blender versions.
- Python compilation and whitespace checks pass. Tests use factory-startup processes and temporary settings, not the user's project or preferences.

No Windows/Linux native run, GUI input-to-paint measurement, third-party custom-node stress test or interactive snippet-placement test was performed in this round. Shortcuts and snippet placement were not changed.

### Reproduction

Run from the repository, with `BLENDER` set to the desired Blender executable and the published `Node_Console_1.2.1.zip` present:

```sh
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/benchmark_search.py -- /tmp/nc-benchmark.json
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/test_search_cache.py -- /tmp/nc-cache.json
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/test_blender_index.py -- /tmp/nc-index.json
```

Raw local reports are retained under ignored `Display/Performance_2026-10-06/`; they are not packaged or published. The color comparison also uses the published 1.2.0 ZIP; run it with `tools/test_node_colors.py`.
