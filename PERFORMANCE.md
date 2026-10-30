# Node Console Performance

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
