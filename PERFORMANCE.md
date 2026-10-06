# Node Console 1.2.2 Search Performance

Date: 2026-10-06. Baseline: published 1.2.1 (`237708f`). This report covers the performance changes included in 1.2.2. The baseline ZIP remains unchanged.

## Changes

- Prepare immutable entry names, categories, aliases and pinyin profiles once per entry instead of on every keystroke. This data is not serialized and replacement entries get fresh caches.
- Bound normalization and word-token caches to 8,192 strings each, and query-priority cache to 256 queries. Clear them with the existing cache-reset path.
- Reuse per-query matches for the weak-pinyin fallback. Blank queries return immediately.
- Obtain runtime capabilities once per index rebuild instead of repeatedly recalculating the runtime signature for individual entries. Index rebuilds still refresh local groups, assets and preferences.
- Do not cache final search results, favorites or settings. No keymap, node identity, persistence schema or ranking changes.

## Measurements

macOS arm64, actual Blender 5.2.2 LTS (`d13f752e3b9c`), factory-startup background process. Baseline and current code run in the same process with separate temporary settings. The baseline ZIP SHA256 is `8f2f57a859bae64c59377c8a413e897054a4b709592d4bbe398e2a76f497fc0a`.

| Editor | Search median before / after | Warm index preparation before / after |
| --- | ---: | ---: |
| Geometry | 19.99 / 8.29 ms | 71.22 / 26.66 ms |
| Shader | 10.60 / 4.59 ms | 51.69 / 27.36 ms |
| Compositor | 10.56 / 4.87 ms | 58.92 / 32.97 ms |

Search timings cover 33 queries, each with and without favorites. Queries include English, Chinese, pinyin, initials, case/space variations, partial input and misses. Warm index timing is the median of three rebuilds. The benchmark indexes contain 517 / 276 / 282 entries, including variants and temporary local groups; these are not unique native-node counts.

These are core-function measurements, not end-to-end popup latency or GUI frame rates. Cold timings are recorded but not used to claim a speedup because Blender/OS initialization and run order affect them. Absolute timings vary by machine and workload.

Blender 5.1.2 also improves: search medians are 18.47 / 8.16 ms (Geometry), 10.39 / 4.68 ms (Shader), and 8.78 / 3.94 ms (Compositor). Warm rebuild medians are 67.19 / 25.54, 52.91 / 24.28, and 52.45 / 28.81 ms respectively.

## Regression Coverage

- Blender 5.2.2: 5,516 generated name/pinyin/initial/prefix queries plus 198 fixed-query/favorite cases have identical complete result order to 1.2.1 (5,714 comparisons, zero differences).
- Blender 5.1.2: 5,023 generated queries plus 198 fixed-query/favorite cases also match exactly (5,221 comparisons). Combined total: 10,935 comparisons, zero differences.
- Blender 5.2.2 and 5.1.2 (`ec6e62d40fa9`): actual search/create checks, menu and registered-type coverage, bilingual display, fallback pinyin, warm-cache identities, same-name asset isolation and preservation of settings/language pass.
- Blender 5.2.2: 1,063 native entry/variant creations and 83 asset creations retain the audited colors; zero failures.
- Both Blender versions: ten cache checks pass, covering preprocessing reuse, live favorites, serialization, changed names/aliases, empty/missed searches, bounded caches, cache reset, local group rename/removal and snippet edits/deletion.
- Python compilation and whitespace checks pass. Tests use factory-startup processes and temporary settings, not the user's project or preferences.

No Windows/Linux native run, GUI input-to-paint measurement, third-party custom-node stress test or interactive snippet-placement test was performed in this round. Shortcuts and snippet placement were not changed. Release-package verification is recorded in `VALIDATION_1.2.2.md`.

## Reproduction

Run from the repository, with `BLENDER` set to the desired Blender executable and the published `Node_Console_1.2.1.zip` present:

```sh
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/benchmark_search.py -- /tmp/nc-benchmark.json
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/test_search_cache.py -- /tmp/nc-cache.json
"$BLENDER" --background --factory-startup --python-exit-code 1 --python tools/test_blender_index.py -- /tmp/nc-index.json
```

Raw local reports are retained under ignored `Display/Performance_2026-10-06/`; they are not packaged or published. The color comparison also uses the published 1.2.0 ZIP; run it with `tools/test_node_colors.py`.
