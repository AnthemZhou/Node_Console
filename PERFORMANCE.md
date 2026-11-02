# Node Console Performance

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
