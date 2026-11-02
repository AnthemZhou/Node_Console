# Node Console

<img width="1920" height="600" alt="节点控制台 02" src="https://github.com/user-attachments/assets/c0468802-5677-4372-92f9-28a31d0f6dd7" />


![Blender](https://img.shields.io/badge/Blender-5.1.2%20%7C%205.2.2%20LTS-f5792a?logo=blender&logoColor=white)
![Version](https://img.shields.io/badge/version-1.5.0-blue)
![Category](https://img.shields.io/badge/category-Node%20Editor-555)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

作者：Anthem  
版本：1.5.0

[下载 / Download](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.0) · [Issues](https://github.com/AnthemZhou/Node_Console/issues)

## Languages / 语言

<details>
<summary>English</summary>

Version 1.5.0 adds Japanese, Korean, Russian and Spanish node search, plus a bug-feedback field in Preferences. Download [Node_Console_1.5.0.zip](https://github.com/AnthemZhou/Node_Console/releases/download/v1.5.0/Node_Console_1.5.0.zip).

Node Console is a custom node search add-on for Blender. It replaces the default `Shift + A` search in the Node Editor. Search by English name, Chinese or pinyin, and use favorites and shortcuts to customize search weighting. macOS and Windows support system Chinese input in the existing custom field; a user has confirmed committed Chinese and node search on Windows. The layout stays compact and is inspired by Blender native search.

### Features

- Search English plus Chinese, Japanese, Korean, Russian or Spanish with bilingual display, independently of Blender's interface language. Chinese pinyin and initials remain supported.
- Supports system Chinese input in the existing search field on macOS and Windows; see platform verification scope below.
- Supports favorite nodes and shortcut nodes. Favorites and shortcuts can customize search weighting and make common nodes faster to create.
- Shows colored node type tags on the left side of search results, making nodes easier to scan by type.
- Supports manual node library refresh, including searchable and categorized Asset Library or externally imported node groups.
- Saves connected node sets as reusable Snippet Nodes that can be found by English or pinyin.
- Check releases, select a version and confirm installation in Preferences; Beta versions are opt-in and disabled by default.

### Chinese Input and Pinyin Search

Version 1.4.5 ranks by official Blender menu paths, search weights and matching rules, including abbreviations and typo tolerance such as `nt` and `niose` for Noise Texture. Chinese, pinyin, initials, relevant favorites and empty-query shortcuts remain available. Editor-specific native weights replace the fixed float/vector preference for `add`. Favorites, transliteration and supplemental candidates are intentional extensions, so exact native-list equality is not promised in every situation.

Version 1.4.6 restores wrapped Output menus, RNA aliases and variants such as vector Map Range, corrects asset paths, and follows native engine, World, tool and experimental-feature conditions. The core scoring formula is unchanged. First-result/empty-outcome agreement reaches 99.4% across 178 comparable probes; strict visible-order agreement is 89.3%. See the [verification scope and limitations](PERFORMANCE.md#146-native-search-alignment).

Version 1.4.7 removes redundant index copying and transliteration, prepares candidates per query language, and reuses recent query matches. Cold index preparation on Blender 5.2.2 improves by approximately 35%–41%; 23,110 full-order comparisons across two Blender versions remain identical. These are internal processing measurements, not equivalent whole-UI speedups; see [performance details](PERFORMANCE.md#147-open-and-input-latency).

On macOS and Windows, press `Shift + A` and use your system Chinese input method to type node names such as `集合` or `噪波`. Composition text is underlined; the system provides candidates. Committed Chinese updates search results. Enter during composition confirms a candidate without creating a node; Escape cancels composition while keeping search open. After committing Chinese, press Enter again to create and place the node.

Version 1.4.5 previews results using in-progress pinyin, switches to Chinese matching on confirmation, and restores the previous query on composition cancellation. Previewing does not confirm an IME candidate.

English and direct pinyin search, such as `instance`, `shili` and `zaobo`, remain available. Chinese can still be pasted (`Command + V` on macOS, `Ctrl + V` on Windows/Linux).

**Platform scope:** Native macOS Chinese input was tested on Apple Silicon, Blender 5.2.2 LTS and macOS Pinyin. The package includes arm64/x86_64 code, but Intel Macs, third-party IMEs and multi-monitor candidate positioning have not been tested live. The Windows backend uses system IMM/Win32 APIs without external Python dependencies. A user confirmed committed Chinese and node search on real Windows hardware; OS, Blender and IME versions were not recorded. Other IMEs, DPI settings, multiple monitors and complete focus/placement workflows still need live testing. Local simulations are not equivalent to Windows hardware coverage. Version 1.4.3 raises Windows CJK by one additional scaled pixel compared with 1.4.2; this adjustment still needs visual confirmation on Windows. Linux retains its original input path. Snippet naming still uses Blender's native text field. Failed backend initialization retains standard search input. See the [input module notes](ime_input/README.md) for Windows testing.

### Multilingual Search (1.5.0)

Choose a secondary language in Preferences > Node Language. English remains searchable in every mode. Search Result Display offers English-only, selected-language-only, or either bilingual order. Upgrades retain Chinese and your saved display mode; Blender's UI language is not changed.

Names, operation variants and menu paths use the installed Blender catalogs with their RNA/menu translation contexts. Missing translations fall back to English. Chinese editorial aliases remain separate from official names. Settings and action text remain primarily English/Chinese; this is not complete UI localization.

- Japanese accepts hiragana/katakana and full-/half-width forms: `のいず` or `ﾉｲｽﾞ` finds `ノイズテクスチャ`. No kanji-reading inference or romaji-to-kanji dictionary is included.
- Korean accepts omitted spaces, initial consonants and unfinished syllables: `노이즈텍`, `ㄴㅇㅈ` and `노ㅇ` find `노이즈 텍스처`.
- Russian accepts case variants and equivalent `е/ё`; Spanish accents may be omitted (`posicion` finds `Posición`), while `n/ñ` remain distinct.
- English remains searchable. Use the corresponding native-language order; Spanish/English queries select the stronger match, favoring English on ties. Favorites update immediately and snippet names support the same input forms. Display names retain their original official spelling.

Search, rendering and input-bridge tests run in isolated Blender instances. They do not certify every language's physical system IME/candidate window on Mac/Windows; see [validation scope](PERFORMANCE.md).

Only the selected catalog/index is prepared. Language-specific cache keys prevent stale translations without clearing favorites, shortcuts, usage or snippet files. The scoring formula is unchanged, but new locales search both English and translated paths, so exact monolingual native-menu order is not promised. See [test scope](PERFORMANCE.md#150-multilingual-search).

Search, node creation and synthetic input drawing are tested. **Real Japanese/Korean system IMEs, candidate windows, keyboard layouts and focus behavior still require Mac/Windows hardware acceptance.** Existing Chinese-input success and simulated commits do not prove every new input method works.

### Install

1. Download `Node_Console_1.5.0.zip` from the release above, not GitHub's automatically generated Source code archives.
2. In Blender, open `Edit > Preferences > Add-ons`.
3. Click `Install...`, then choose the downloaded zip file.
4. Enable `Node Console`.

### Usage

1. Open any node editor.
2. Press `Shift + A`.
3. Type an English name or pinyin, such as `instance`, `shili`, `noise`, or `zaobo`; macOS and Windows users can also use a Chinese IME.
4. Press Enter, or click a result to create the node.
5. Move the mouse to choose the node position.
6. Click the left mouse button, or press Enter to place the node.
7. Right-click a result to add or remove favorites and shortcuts.

An empty query shows shortcuts as regular vertical node rows with the selected category colors and bilingual display mode. Drag a row and release to save its order; Escape, right-click or an outside drop cancels. Geometry, Shader and Compositor editors keep independent orders. Typing still searches nodes directly, without opening the native Add menu first.

Three subtle horizontal lines at the right of each shortcut row indicate dragging; the entire row remains draggable. Pressing gently brightens it, dragging lifts it under the pointer while neighbors slide aside, and releasing settles it into place. Regular search and snippet results do not show reorder grips.

### Snippet Nodes

1. Select the nodes or frame you want to reuse in a node editor.
2. Press `Ctrl + Shift + G`; on macOS, the default is `Command + Shift + G`.
3. Enter a required snippet name and choose a category. If the selection has no frame, Node Console creates one automatically.
4. Press `Shift + A` to open Node Console, then press the backtick key `` ` `` above Tab to enter Snippet Node mode. The `·` character produced by a Chinese input method is also supported.
5. Search by the snippet name or its pinyin, then press Enter or click the result to insert the complete node set with its internal links.
6. Press `` ` `` or `·` again to return to regular node search. The current query is preserved while switching modes.
7. Right-click a snippet result to add or remove its favorite status, or to delete the snippet.

Snippet Nodes are stored in an external JSON library file. Preferences provide controls for the save shortcut, the library path, and the expandable list of saved snippets.

`None` in a result means no category was assigned, not an error. Choose an editor-appropriate Category in the save dialog; internal links provide an inferred terminal-node category, while unlinked selections default to None. Filter, Mask and Distort are compositor-only choices. Existing entries can currently be viewed or deleted in Preferences; editing a saved category directly is not yet supported, and updates do not rewrite saved categories.

### Preferences

- `Node Language`: choose Chinese, Japanese, Korean, Russian or Spanish; English is always searchable.
- `Search Result Display`: choose English, the selected language, or either bilingual order.
- `Console Size`: adjusts the search panel size from 0.5 to 2.0.
- `Console Width`: adjusts the horizontal search panel width, defaults to 400, and stays in sync with right-edge dragging in the search panel.
- `Show Cached Asset Nodes`: shows cached Asset Library node groups in search results.
- `Category Color Display`: chooses colored category blocks, left-side color lines, or no category color decoration.
- `Refresh Asset Index`: rebuilds the asset node cache manually.
- `Shortcut`: changes the key and modifiers used to open Node Console.
- `Save Snippet Node Shortcut`: changes the shortcut used to save the selected node set.
- `Snippet Libraries`: shows the snippet JSON library location and saved snippets.
- `Favorites`: lists favorite nodes and lets you remove them.
- `Shortcuts`: lists shortcut nodes and lets you remove or reorder them.

### Online Updates

Click Update in Node Console Preferences to list [GitHub releases](https://github.com/AnthemZhou/Node_Console/releases) with installation packages. Checking only reads metadata. Choose a version, click the download icon (Install Selected Version), then confirm before anything is downloaded or replaced. The current version is marked and cannot be reinstalled. There are no startup network checks.

The updater contains the current version, Beta checkbox, widened release selector, Update button and install icon with tooltips. Check/download/error status stays inline after the version. Narrow windows use a stable two-row layout; status changes do not push content down, and native widgets truncate text when space is limited. It keeps the three newest version choices for the current channel, plus Other Versions, which opens GitHub Releases without changing the installation target or starting a download. Default to an upgrade or the installed version, never a downgrade; label older stable releases, Beta and RC separately.

Starting with 1.4.5, choices include a brief localized highlight in parentheses, covering releases from 1.3.0 (online updates) and 1.3.1 (hot updates) onward. Tooltips retain the full text without adding layout rows.

- Accept Beta Versions is off by default. Enable it and check again to include published GitHub prereleases. No Beta options are fabricated when none exist; changing the checkbox never installs or downgrades the add-on.
- Beta installation and downgrade dialogs display appropriate warnings. Returning from Beta to a stable release is supported with backup and confirmation. Downgrading to an older version such as 1.4.0 also restores that version's older update interface.
- 1.5.0 is stable and available with Beta disabled. Historical prereleases remain accessible through Other Versions.

To publish a Beta, tag it as e.g. `v1.4.2-beta.1`, attach `Node_Console_1.4.2-beta.1.zip`, mark the GitHub release as `Pre-release` and publish it. The package must use `ADDON_VERSION = "1.4.2-beta.1"` and `bl_info["version"] = (1, 4, 2)`; rebuild the macOS input resource for the full version too. Use `v1.4.2-rc.1` for RC builds. A title-only change or source ZIP is insufficient. The user's Beta setting filters manual update checks; it never triggers automatic installation.

Keep the version's `node-console-summary` CHANGELOG comment in its GitHub release body and maintain `addon_updater.RELEASE_HIGHLIGHTS` with its Chinese translation. Example standalone line: `<!-- node-console-summary: {"zh":"首次搜索提速","en":"Faster first search"} -->`. Installed versions from 1.4.5 can then show future highlights before installation without extra requests. Limits are 32 Chinese / 72 English characters; keep summaries shorter where possible. Missing/invalid metadata falls back to known historical highlights or See release notes, without affecting release eligibility.

- Enable Allow Online Access in Blender Preferences > System. The add-on never changes this permission for you.
- A separate process handles downloads. Network errors, invalid packages and incompatible Blender versions leave the installation untouched.
- A local backup is kept before replacement. Favorites, shortcuts, ordering, usage, settings and snippet libraries are preserved. The folder button after a successful update opens the backup at `.node-console-update-*/previous` beside the installation.
- Updates activate without restarting Blender. Activation waits for node search, placement or snippet naming to finish, then reloads only Node Console. Blender and other add-ons' keymaps are not reset or re-registered. Failed activation attempts to restore the previous version; if recovery fails, a message asks you to restart and check the backup.
- Git source checkouts cannot be replaced through this button. Install a version containing the updater before using this feature for the first time.
- Existing 1.4.0 users can upgrade via the original Update button; version selection appears after installing 1.4.1. Updating from 1.3.0 still requires one restart; 1.3.1 and later support subsequent hot activation.

### Bug Feedback

The Bug Feedback section at the bottom of Preferences uses a native Blender text field. Its muted placeholder disappears when you type. Describe the problem and reproduction steps, then click Open GitHub Issue. **Sign in to GitHub and confirm submission on the web page to publish a public issue.** Typing does not send anything automatically.

The draft contains only your text, Node Console/Blender versions, platform and selected node language. It does not read or upload scenes, files, other add-on lists or preferences. Text stays in memory for the current session, outside saved settings, and is retained when opening the page or on errors. Overlong reports ask you to shorten the text; add further details and screenshots on GitHub. Never include passwords, tokens or private project data in a public issue.

### Notes

- Node Console is released as a regular Blender add-on zip.
- The add-on does not modify Blender language files, node labels, or socket labels.
- Version 1.4.4 lowers macOS Latin input and Latin preedit by two scaled units without moving Chinese text. Completed indexes are reused to reduce search-opening preparation. The cache rebuilds once after updating; subsequent first and repeated opens can reuse it. Favorites, usage weights and settings remain intact. See [performance results](PERFORMANCE.md) for measurements and scope.
- Version 1.2.2 optimizes matching and index preparation. Median core search time is approximately 54%–59% lower on Blender 5.2.2; 10,935 queries across two Blender versions retain identical results and ordering. See [performance results](PERFORMANCE.md).
- Version 1.2.1 corrects shader, script, selected geometry/output and Split Toning asset colors. Shader snippets now use dedicated shader green. Runtime registration and native creation checks still determine which nodes are offered in each editor.
- Chinese labels use the running Blender's official Simplified Chinese catalog and translation contexts without changing the UI language. Editorial search aliases are stored separately. Search supports English, Chinese, full pinyin and complete initials, such as `Mesh Bevel`, `网格倒角`, `wanggedaojiao` and `wgdj`.
- After upgrading Blender, use Refresh Asset Index to discover new bundled node groups. Only locally readable `.blend` assets are indexed; undownloaded online assets are not presented as directly creatable nodes.
- See the [changelog](CHANGELOG.md) for changes to node support, translation handling and category colors.

</details>

<details>
<summary>日本語</summary>

Node Console 1.5.0 は Blender のノード検索アドオンです。ジオメトリ、シェーダー、コンポジターの各ノードエディターで、英語と選択した言語の両方からノードを検索できます。

### インストールと言語設定

1. [リリースページ](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.0)から `Node_Console_1.5.0.zip` をダウンロードします。GitHub の Source code ZIP ではありません。
2. Blender の環境設定で「ディスクからインストール」を選び、ZIP をインストールして Node Console を有効にします。動作確認済みバージョンは 5.1.2 / 5.2.2 LTS です。
3. アドオン設定の `Node Language` を `日本語` にします。`Search Result Display` で英語のみ、日本語のみ、または両方の表示順を選べます。Blender 自体の表示言語は変更しません。

### 検索と操作

- ノードエディターで `Shift + A` を押して検索します。英語は常に検索でき、日本語ではひらがな・カタカナ、全角・半角を同一視します。`のいず` と `ﾉｲｽﾞ` は `ノイズテクスチャ` に一致します。漢字の読みの推測やローマ字から漢字への変換辞書は含まれません。
- Enter またはクリックでノードを作成し、マウスで位置を決めてクリックまたは Enter で配置します。
- 結果を右クリックすると、お気に入りやショートカットを登録できます。検索欄が空のときに表示されるショートカット行はドラッグで並べ替えられます。順序はエディターごとに保存されます。
- ノード名はインストール済み Blender の公式翻訳を使い、未翻訳の名前は英語で表示します。検索結果の順序はネイティブ検索に近づけていますが、追加の言語マッチやお気に入りにより完全一致は保証しません。

### スニペットと更新

選択したノードやフレームを `Ctrl + Shift + G`（macOS は `Command + Shift + G`）で名前・カテゴリ付きのスニペットとして保存できます。検索欄でバッククォートキー（Tab の上のキー）を押すと通常のノード検索とスニペット検索を切り替え、入力済みの文字は保持されます。`·` も使えます。ライブラリは外部 JSON ファイルに保存され、設定から場所や保存済み項目を確認できます。

設定の更新ボタンで GitHub のリリースを確認し、バージョンを選んでインストールを確定します。Beta は任意で、初期状態では無効です。更新前のバックアップを保持し、お気に入りやライブラリを消去しません。

### 不具合の報告と検証範囲

設定の一番下の `Bug Feedback` に問題と再現手順を入力し、`Open GitHub Issue` を押します。薄い文字の入力ヒントは入力すると消えます。GitHub にログインして草稿を確認・送信すると公開 Issue になります。入力中の自動送信はありません。草稿には入力内容、アドオンと Blender のバージョン、プラットフォーム、ノード言語だけを含め、シーンやファイルはアップロードしません。入力内容は現在のセッションのメモリにのみ保持します。

検索・ノード作成・描画は分離した Blender 環境で検証済みです。ただし、日本語・韓国語の実際のシステム IME 候補ウィンドウや全キーボード配置を Mac/Windows で網羅的に検証したわけではありません。設定画面と操作メッセージは主に英語・中国語のままです。[検証範囲](PERFORMANCE.md)と[変更履歴](CHANGELOG.md)も参照してください。

</details>

<details>
<summary>한국어</summary>

Node Console 1.5.0은 Blender용 노드 검색 애드온입니다. 지오메트리, 셰이더, 컴포지터 노드 편집기에서 영어와 선택한 언어로 노드를 검색할 수 있습니다.

### 설치와 언어 설정

1. [릴리스 페이지](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.0)에서 `Node_Console_1.5.0.zip`을 다운로드합니다. GitHub의 Source code ZIP은 설치 패키지가 아닙니다.
2. Blender 환경설정에서 디스크로부터 설치를 선택하고 ZIP을 설치한 뒤 Node Console을 활성화합니다. 검증한 Blender 버전은 5.1.2 / 5.2.2 LTS입니다.
3. 애드온 설정의 `Node Language`를 `한국어`로 선택합니다. `Search Result Display`에서 영어만, 한국어만 또는 두 언어의 표시 순서를 선택할 수 있습니다. Blender 자체의 인터페이스 언어는 바뀌지 않습니다.

### 검색과 조작

- 노드 편집기에서 `Shift + A`를 누르고 검색합니다. 영어는 항상 검색할 수 있으며, 한국어는 띄어쓰기 생략, 초성, 입력 중인 미완성 음절을 지원합니다. `노이즈텍`, `ㄴㅇㅈ`, `노ㅇ`으로 `노이즈 텍스처`를 찾을 수 있습니다.
- Enter 또는 결과 클릭으로 노드를 생성한 뒤, 마우스로 위치를 정하고 클릭 또는 Enter로 배치합니다.
- 결과를 우클릭하면 즐겨찾기나 바로가기를 추가할 수 있습니다. 검색어가 없을 때 나타나는 바로가기 행은 드래그로 정렬할 수 있으며, 순서는 노드 편집기별로 저장됩니다.
- 이름은 설치된 Blender의 공식 번역을 사용하고, 번역이 없으면 영어로 표시합니다. 검색 순서는 기본 검색에 가깝게 유지하지만, 언어별 추가 일치와 즐겨찾기 때문에 항상 완전히 같지는 않습니다.

### 스니펫과 업데이트

노드나 프레임을 선택하고 `Ctrl + Shift + G`(macOS: `Command + Shift + G`)를 눌러 이름과 범주를 지정한 스니펫으로 저장합니다. 검색창에서 백틱 키(Tab 위의 키)를 누르면 일반 노드 검색과 스니펫 검색을 전환하며, 입력한 검색어는 유지됩니다. `·`도 사용할 수 있습니다. 라이브러리는 외부 JSON 파일에 저장되고 환경설정에서 경로와 저장 항목을 확인할 수 있습니다.

환경설정의 업데이트 버튼으로 GitHub 릴리스를 확인하고 버전을 선택한 뒤 설치를 확정합니다. Beta 수신은 선택 사항이며 기본값은 꺼짐입니다. 업데이트 전 백업을 보관하며 즐겨찾기나 라이브러리를 지우지 않습니다.

### 버그 제보와 검증 범위

환경설정 맨 아래의 `Bug Feedback`에 문제와 재현 방법을 입력하고 `Open GitHub Issue`를 누릅니다. 흐린 안내 문구는 입력하면 사라집니다. GitHub에 로그인해 초안을 확인하고 제출해야 공개 Issue가 생성됩니다. 입력 중 자동 전송하지 않습니다. 초안에는 작성한 내용, 애드온/Blender 버전, 플랫폼, 노드 언어만 포함하며 장면이나 파일을 업로드하지 않습니다. 입력 내용은 현재 세션의 메모리에만 보관됩니다.

검색, 노드 생성, 화면 그리기는 격리된 Blender 환경에서 검증했습니다. 다만 한국어·일본어 시스템 IME의 실제 후보 창, 모든 키보드 배열과 포커스 동작을 Mac/Windows에서 모두 검증한 것은 아닙니다. 설정 화면과 조작 메시지는 주로 영어·중국어입니다. [검증 범위](PERFORMANCE.md)와 [변경 기록](CHANGELOG.md)을 참고하세요.

</details>

<details>
<summary>Русский</summary>

Node Console 1.5.0 позволяет искать и добавлять узлы Blender на английском и выбранном языке. Поддерживаются редакторы геометрических узлов, шейдеров и композитинга.

### Установка и язык

1. Скачайте `Node_Console_1.5.0.zip` со [страницы релиза](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.0), а не автоматически созданный архив Source code.
2. В настройках Blender выберите установку расширения с диска, укажите ZIP и включите Node Console. Проверенные версии Blender: 5.1.2 и 5.2.2 LTS.
3. В настройке `Node Language` выберите `Русский`. Параметр `Search Result Display` задаёт английские, русские или двуязычные названия и их порядок. Язык интерфейса самого Blender не меняется.

### Поиск и работа с узлами

- Нажмите `Shift + A` в редакторе узлов. Английские названия доступны всегда. Русский поиск не зависит от регистра и считает `е` и `ё` эквивалентными: например, `объем` находит названия с `Объём`. Мягкий и твёрдый знаки не удаляются.
- Нажмите Enter или щёлкните по результату, затем выберите положение мышью и подтвердите щелчком или Enter.
- Через контекстное меню результата можно добавить узел в избранное или в список быстрого доступа. При пустом запросе этот список отображается строками; перетаскивание меняет порядок. Каждый редактор хранит свой порядок.
- Названия берутся из официального перевода установленного Blender; при отсутствии перевода используется английское название. Порядок близок к встроенному поиску, но дополнительные языковые совпадения и избранное могут его изменять.

### Наборы узлов и обновления

Выберите узлы или рамку и нажмите `Ctrl + Shift + G` (на macOS: `Command + Shift + G`), чтобы сохранить набор как Snippet Node с именем и категорией. В поисковой строке клавиша обратной кавычки над Tab переключает поиск обычных узлов и сохранённых наборов, сохраняя запрос. Символ `·` также поддерживается. Библиотека хранится во внешнем JSON-файле; путь и сохранённые наборы доступны в настройках.

Кнопка обновления проверяет релизы GitHub. Выберите версию и подтвердите установку. Beta-версии включаются отдельно и по умолчанию скрыты. Перед заменой сохраняется резервная копия; избранное и библиотеки не очищаются.

### Сообщение об ошибке и ограничения

Внизу настроек заполните `Bug Feedback` и нажмите `Open GitHub Issue`. Серый текст-подсказка исчезает при вводе. Откроется черновик: войдите в GitHub, проверьте его и подтвердите отправку, чтобы создать публичный Issue. Автоматической отправки при наборе нет. Черновик содержит только ваш текст, версии Node Console и Blender, платформу и язык узлов. Сцены и файлы не загружаются; текст хранится только в памяти текущего сеанса.

Поиск, создание узлов и отрисовка проверены в изолированных экземплярах Blender. Это не полная проверка всех системных методов ввода, раскладок и окон кандидатов на Mac/Windows, особенно для японского и корейского. Настройки и служебные сообщения пока преимущественно на английском и китайском. Подробнее: [проверки](PERFORMANCE.md) и [история изменений](CHANGELOG.md).

</details>

<details>
<summary>Español</summary>

Node Console 1.5.0 permite buscar y añadir nodos de Blender en inglés y en el idioma seleccionado. Funciona en los editores de nodos de geometría, sombreado y composición.

### Instalación e idioma

1. Descarga `Node_Console_1.5.0.zip` desde la [página de la versión](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.0), no los archivos Source code generados por GitHub.
2. En las preferencias de Blender, instala el ZIP desde disco y activa Node Console. Las versiones de Blender comprobadas son 5.1.2 y 5.2.2 LTS.
3. Selecciona `Español` en `Node Language`. En `Search Result Display` puedes mostrar inglés, español o ambos idiomas en el orden que prefieras. No se cambia el idioma de la interfaz de Blender.

### Búsqueda y uso

- Pulsa `Shift + A` en un editor de nodos. El inglés siempre está disponible. La búsqueda en español admite mayúsculas, minúsculas y palabras sin tildes: `posicion` encuentra `Posición`. Se mantiene la distinción entre `n` y `ñ`.
- Pulsa Enter o haz clic en un resultado para crear el nodo; mueve el ratón y confirma su posición con un clic o Enter.
- Haz clic derecho en un resultado para añadirlo a favoritos o a los accesos rápidos. Con la búsqueda vacía, los accesos rápidos aparecen como filas que puedes ordenar arrastrándolas. Cada editor mantiene su propio orden.
- Se usan las traducciones oficiales del Blender instalado; los nombres sin traducción aparecen en inglés. El orden se aproxima al buscador nativo, pero las coincidencias adicionales y los favoritos pueden producir diferencias.

### Conjuntos de nodos y actualizaciones

Selecciona nodos o un marco y pulsa `Ctrl + Shift + G` (macOS: `Command + Shift + G`) para guardar un Snippet Node con nombre y categoría. En el buscador, la tecla de acento grave situada sobre Tab alterna entre nodos normales y conjuntos guardados, conservando el texto. También se admite `·`. La biblioteca se guarda en un archivo JSON externo; puedes consultar su ruta y los elementos guardados en las preferencias.

El botón de actualización consulta las versiones publicadas en GitHub. Selecciona una versión y confirma la instalación. Las versiones Beta son opcionales y están desactivadas por defecto. Se conserva una copia de seguridad antes de sustituir el complemento, sin borrar favoritos ni bibliotecas.

### Informar de errores y alcance de las pruebas

Al final de las preferencias, escribe el problema y los pasos para reproducirlo en `Bug Feedback` y pulsa `Open GitHub Issue`. El texto gris de ayuda desaparece al escribir. Se abre un borrador: debes iniciar sesión en GitHub, revisarlo y confirmar el envío para crear una incidencia pública. No se envía nada automáticamente al escribir. El borrador solo incluye tu texto, las versiones del complemento y Blender, la plataforma y el idioma de los nodos. No se suben escenas ni archivos; el texto solo se conserva en la memoria de la sesión actual.

La búsqueda, la creación de nodos y el dibujo de la interfaz se han probado en instancias aisladas de Blender. No se han verificado exhaustivamente todos los métodos de entrada, teclados y ventanas de candidatos de Mac/Windows, especialmente los IME japonés y coreano. Los ajustes y mensajes siguen principalmente en inglés y chino. Consulta las [pruebas y limitaciones](PERFORMANCE.md) y el [registro de cambios](CHANGELOG.md).

</details>

## 中文

1.5.0 新增日语、韩语、俄语和西班牙语节点搜索，以及偏好设置中的问题反馈入口。安装包：[Node_Console_1.5.0.zip](https://github.com/AnthemZhou/Node_Console/releases/download/v1.5.0/Node_Console_1.5.0.zip)。

Node Console 是一个 Blender 节点搜索插件。它会替换节点编辑器里的 `Shift + A` 搜索，让你可以用英文、中文或拼音搜索节点，并通过 favorite 和 shortcut 自定义搜索权重。macOS 和 Windows 可在同一自绘框中使用系统输入法输入中文；Windows 中文上屏与检索已获用户实机确认。界面保持紧凑，视觉风格接近 Blender 原生搜索。

### 功能

- 支持英文＋所选语言（中文、日语、韩语、俄语、西班牙语）搜索和双语显示，不依赖当前 Blender 界面语言；中文保留拼音和首字母检索。
- macOS 和 Windows 支持在现有搜索框内使用系统中文输入法；平台验证范围见下文。
- 支持收藏节点和快捷节点。favorite 和 shortcut 可以自定义搜索权重，也方便快速创建常用节点。
- 在搜索结果左侧显示节点类型颜色标签，方便根据节点类型快速检索。
- 支持手动刷新节点库，可以检索并分类 Asset Library 和外部导入的节点组。
- 支持将一组节点及其连接保存为可复用的「组合点」，并通过英文或拼音快速检索。
- 偏好设置支持检查版本、选择版本并确认安装；可选加入 Beta 测试，默认只显示稳定版。

### 中文输入与拼音搜索

1.4.5 按 Blender 官方菜单路径、搜索权重与匹配规则排序，支持英文缩写和容错，例如 `nt`、`niose` 可以找到 Noise Texture。中文、全拼、首字母、收藏置顶与空输入快捷列表继续保留。不同编辑器的官方权重不同，`add` 不再使用统一写死的浮点/矢量优先顺序。收藏、拼音和菜单外补充节点属于增强结果，因此不承诺所有情况下与原生列表完全相同。

1.4.6 补齐被菜单包装遗漏的输出节点、RNA 别名与矢量版「映射范围」等变体，修正资产路径，并遵循当前引擎、World、工具模式及实验开关的官方菜单条件。核心评分公式不变。178 组可比查询实测首条或空结果一致率为 99.4%，严格前列顺序一致率为 89.3%；抽样范围与局限见[验证说明](PERFORMANCE.md#146-native-search-alignment)。

1.4.7 减少索引读取与拼音准备的冗余工作，按查询语言准备候选，并复用最近查询的匹配结果。Blender 5.2.2 首次无缓存索引准备耗时降低约 35%–41%；两版 Blender 共 23,110 次完整结果顺序对比一致。以上是内部计算测试，不代表整个界面同比提速，详见[性能说明](PERFORMANCE.md#147-open-and-input-latency)。

macOS 和 Windows 用户可以按 `Shift + A` 后，直接用系统中文输入法输入「集合」「噪波」等节点名。组词中的拼音带下划线，候选词由系统输入法提供；确认中文上屏后更新搜索结果。组词时的回车只确认候选词，不会误创建节点；Esc 先取消组词，搜索框仍然保留。中文上屏后，再按回车即可创建并放置节点。

1.4.5 也会在组词过程中按当前拼音预览结果，无需等到中文确认后才出现列表；确认中文后使用中文排序，取消组词后恢复原查询。预览不会替你确认输入法候选词。

英文和拼音检索仍然保留，例如 `instance`、`shili`、`zaobo`，不必先转换成中文。也支持粘贴中文节点名后检索（macOS：`Command + V`，Windows/Linux：`Ctrl + V`）。

**平台范围：** macOS 原生中文输入实测于 Apple Silicon Mac、Blender 5.2.2 LTS 和系统拼音输入法。安装包同时包含 arm64/x86_64 原生模块，但 Intel Mac、第三方输入法及多显示器候选框位置尚未实机验证。Windows 实现直接调用系统 IMM/Win32 接口，不需要安装 Python 模块；用户已确认真实 Windows 环境下中文上屏及节点检索。具体系统、Blender 和输入法版本未记录，其他输入法、显示缩放、多显示器及完整焦点/放置流程仍待进一步实测；本地模拟测试不等同于 Windows 实机覆盖。1.4.3 在 1.4.2 基础上将 Windows 中文再上移一个缩放像素，此次位置微调仍需用户视觉复核。Linux 仍使用原有英文、拼音和中文粘贴方式。组合点命名继续使用 Blender 原生输入框。原生后端初始化失败时保留原有搜索输入方式。Windows 实测方法见 [输入模块说明](ime_input/README.md)。

### 多语言节点搜索（1.5.0）

在偏好设置的「节点语言 / Node Language」选择中文、日本語、한국어、Русский 或 Español。英文始终可检索；「搜索结果显示」可选择仅英文、仅所选语言，或两种语言的前后顺序。升级默认保留中文和原显示设置，不改变 Blender 自身的界面语言。

节点、操作变体及搜索菜单路径使用当前 Blender 安装包的官方翻译，按 RNA/菜单翻译上下文读取；缺译时回退英文。中文历史译名和人工别名仍只作为中文搜索增强。插件设置和操作提示仍主要为中英界面，本次不是所有 UI 文案的完整翻译。

- 日语支持平假名/片假名、全角/半角互搜，例如 `のいず`、`ﾉｲｽﾞ` 都能找到 `ノイズテクスチャ`。不推测汉字读音，也不内置罗马音转汉字词典。
- 韩语支持省略空格、声母缩写和输入中的未完成音节，例如 `노이즈텍`、`ㄴㅇㅈ`、`노ㅇ` 能找到 `노이즈 텍스처`。
- 俄语支持大小写与 `е/ё` 等价搜索；西班牙语可以省略重音，如 `posicion` 匹配 `Posición`，但仍区分 `n/ñ`。
- 英文始终可搜。按查询语言使用相应官方菜单顺序；西语与英文同为拉丁文字，选择匹配更强的一侧，同分优先英文。收藏实时置顶，组合点名称也支持上述输入形式。显示仍保留官方文字，不显示规范化后的搜索键。

这些增强已在隔离 Blender 中验证搜索、绘制和输入桥接流程，但不代表四种语言的所有系统输入法候选窗都已完成 Mac/Windows 实机验收；详见 [验证范围](PERFORMANCE.md)。

只加载所选语言的词典和索引，不在首次打开时准备全部语言。切换语言后按需重建缓存，节点标识、收藏、快捷节点、使用记录和组合点文件保持不变。评分公式不变；新语言同时匹配英文和译名，因此不承诺与单语言原生列表逐项同序。中文模式的完整顺序回归见[测试范围](PERFORMANCE.md#150-multilingual-search)。

新增语言已经进行搜索、创建及合成输入事件的绘制测试，但**日语、韩语系统输入法的真实候选窗、键盘布局和焦点流程仍需 Mac/Windows 用户实机验收**；不会把中文输入成功或模拟上屏等同于这些输入法全部通过。

### 安装

1. 从上方 Release 下载 `Node_Console_1.5.0.zip`，不要使用 GitHub 自动生成的 Source code 压缩包。
2. 在 Blender 中打开 `编辑 > 偏好设置 > 插件`。
3. 点击 `安装...`，选择下载的 zip 文件。
4. 启用 `Node Console`。

### 使用

1. 打开任意节点编辑器。
2. 按 `Shift + A`。
3. 输入英文或拼音，例如 `instance`、`shili`、`noise`、`zaobo`；macOS 和 Windows 也可用中文输入法输入节点名。
4. 按 Enter，或点击搜索结果来创建节点。
5. 移动鼠标决定节点位置。
6. 点击鼠标左键，或按 Enter 落位。
7. 右键搜索结果，可以添加或取消收藏，也可以添加快捷节点。

空搜索时的快捷节点使用纵向普通节点行，沿用类目颜色和中英文显示模式。可拖动节点行排序，松开保存；按 Esc、右键或拖到列表外松开可取消。顺序按几何、材质、合成编辑器分别保存。输入文字后仍是正常节点搜索，不先弹出官方添加菜单。

快捷节点行右侧的三条浅色横线表示可拖动；整行均可按住拖动。按下后轻微提亮，拖动行跟随鼠标，相邻行平滑让位，松开后归位。普通搜索结果和组合点结果不显示排序标记。

### 组合点

1. 在节点编辑器中选中需要复用的节点或 Frame。
2. 按 `Ctrl + Shift + G`；macOS 默认按 `Command + Shift + G`。
3. 输入组合点名称并选择类目。名称用于后续英文或拼音检索；没有 Frame 时，插件会自动创建 Frame。
4. 按 `Shift + A` 打开 Node Console，然后按键盘 Tab 上方的反引号键 `` ` `` 进入「组合点」模式。中文输入法产生的 `·` 同样有效。
5. 输入组合点名称或拼音，按 Enter 或点击结果，将整组节点及其内部连接放回当前节点编辑器。
6. 再按一次 `` ` `` / `·` 可返回普通节点搜索；切换模式时会保留当前输入内容。
7. 右键组合点结果，可以添加或取消收藏，也可以删除该组合点。

组合点保存在外部 JSON 库文件中。你可以在偏好设置中调整保存组合点的快捷键、查看组合点库路径，并展开组合点列表进行管理。

结果中的「无」表示保存时未指定类目（`None`），并非错误。保存弹窗的「类目」下拉框按当前编辑器列出适用类目，可手动选择；有内部连线时按末端节点推断默认类目，没有连线时默认「无」。滤镜、遮罩和扭曲仅出现在合成编辑器的类目列表中。目前已保存条目只能在偏好设置中查看或删除，尚无直接编辑类目的入口；升级不会改写已有分类。

### 偏好设置

- `节点语言`（Node Language）：选择中文、日语、韩语、俄语或西班牙语，英文始终可搜索。
- `搜索结果显示`（Search Result Display）：选择 English、所选语言、English / 所选语言 或 所选语言 / English。
- `搜索窗口大小`（Console Size）：调整搜索窗口整体尺寸，范围是 0.5 到 2.0。
- `搜索窗口宽度`（Console Width）：调整搜索窗口横向宽度，默认是 400，也可以在搜索框右侧拖拽后同步保存。
- `显示缓存的资产节点`（Show Cached Asset Nodes）：在搜索结果中显示已缓存的资产节点组。
- `类目颜色显示`（Category Color Display）：选择类目颜色底块、左侧颜色竖线或关闭类目颜色装饰。
- `刷新资产索引`（Refresh Asset Index）：手动刷新资产节点缓存。
- `快捷键`（Shortcut）：修改打开 Node Console 的快捷键。
- `保存组合点快捷键`（Save Snippet Node Shortcut）：修改保存当前选中节点组合的快捷键。
- `组合点库`（Snippet Libraries）：查看组合点 JSON 库文件的位置和已保存的组合点。
- `收藏`（Favorites）：查看并删除收藏节点。
- `快捷节点`（Shortcuts）：查看、删除或调整快捷节点顺序。

### 在线更新

在 Node Console 偏好设置中点击「更新」，读取 [GitHub Releases](https://github.com/AnthemZhou/Node_Console/releases) 中有安装包的版本；这一步不会下载安装包或替换插件。在版本下拉框选择目标，再点击下载图标（安装所选版本），确认后才下载、校验并替换。当前安装版本会标注，不能重复安装同一版本；不会在启动 Blender 时自动联网。

更新栏包含当前插件版本、Beta 开关、加宽的版本选择框、更新按钮及安装图标；检查、下载和错误状态直接显示在版本号后方，不另起一行。窄窗口使用固定双行布局，状态变化不推动下方内容；空间不足时文字由原生界面截短。鼠标悬停在图标上可查看操作名称。列表按版本号保留当前通道最近三个版本选项，另有「其他版本」入口可打开 GitHub Releases 手动选择下载，不会改变当前选择或开始安装。默认选择更新版本，没有更新则停留在当前版本，不自动选中旧版。旧正式版、Beta 和 RC 会分别标记。

- 「接受 Beta 测试版本」默认关闭。勾选后重新检查，才会列出 GitHub 标记为 Pre-release 的版本；没有已发布的 Beta 时不会虚构选项。勾选或取消本身不会安装、降级或切换版本。
- 选择 Beta 或较旧版本时，确认框会显示风险或回退提示。允许手动从 Beta 回到稳定版，仍先备份再替换。回退到 1.4.0 等旧版本时，更新界面也会恢复为该版本的样式。
- 1.5.0 为正式版，关闭 Beta 开关也能获取；历史预发布版仍可在「其他版本」中找到。

1.4.5 起，版本选项同时显示简短更新重点，例如 `1.4.4（首次搜索提速，旧正式版）`；已补齐 1.3.0 在线更新、1.3.1 热更新以来的版本。摘要跟随界面语言，悬停提示保留完整说明，不增加更新栏行数。

发布 Beta 时，使用完整版本标签（例如 `v1.4.2-beta.1`），上传同版本安装包 `Node_Console_1.4.2-beta.1.zip`，并在 GitHub Release 勾选 `Pre-release` 后发布。包内 `ADDON_VERSION` 需为 `1.4.2-beta.1`，`bl_info` 为 `(1, 4, 2)`；macOS 原生输入资源也需按完整版本重新构建。RC 同理使用 `v1.4.2-rc.1`。仅改标题或上传源码 ZIP 不会被识别为可安装的测试版。用户手动检查更新时会按 Beta 开关筛选，不会后台自动安装。

发布新版本时，在 Release 正文中保留该版 CHANGELOG 的 `node-console-summary` 注释，并同步维护 `addon_updater.RELEASE_HIGHLIGHTS` 及中文译文。例如单独一行 `<!-- node-console-summary: {"zh":"首次搜索提速","en":"Faster first search"} -->`。已安装的 1.4.5 及后续版本即可在安装前读取新版本的说明，无需额外联网；摘要限中文 32 字、英文 72 字，建议更短。缺失或格式不合法时使用内置历史摘要，未知版本显示「详见更新说明」，不编造重点、不影响安装资格。

- 需要在 Blender 的 `偏好设置 > 系统` 中允许在线访问；不会替你修改该权限。
- 下载在独立进程中执行，不占用搜索界面的主线程。网络失败、损坏的包或不兼容的 Blender 版本会提示错误，不替换插件。
- 替换前保留本地备份；收藏、快捷节点、排序、使用记录和组合点库不清空。成功后的文件夹按钮可打开旧文件备份，备份保留在插件目录旁的 `.node-console-update-*/previous` 中。
- 下载完成后自动热更新，无需重启 Blender。搜索、节点放置或组合点命名尚未结束时会等待，完成后只重载 Node Console，不重置或重新注册 Blender 和其他插件的快捷键。新版启用失败会尝试恢复原版本；若无法自动恢复，界面会提示重启并检查备份。
- Git 源码工程不接受自动替换。首次使用此按钮需要先安装包含此功能的版本。
- 已安装 1.4.0 的用户可通过原来的「更新」按钮升级到 1.4.1；升级后才出现版本选择和 Beta 开关。从 1.3.0 的旧更新器升级仍需首次重启，1.3.1 起支持后续热加载。

### 问题反馈

偏好设置最下方的「问题反馈」使用 Blender 原生输入框：空白时显示灰色提示，输入后提示消失。填写遇到的问题和复现步骤，再点击「在 GitHub 中继续」。浏览器会打开预填好的 Issue 草稿；**需要登录 GitHub 并在网页确认提交后，你的反馈才会成为公开 Issue**，不会在键入时自动发送。

草稿仅附带你填写的文字、Node Console/Blender 版本、平台及节点语言，不读取或上传场景、文件、其他插件清单或偏好设置。输入只暂存在当前会话中，不写入设置文件；打开网页或发生错误时不会清空。内容超出链接长度限制时会提示精简，你可以在 GitHub 中继续补充文字和截图。不要在公开反馈中包含密码、令牌或私人项目资料。

### 说明

- Node Console 以普通 Blender 插件 zip 格式发布。
- 插件不会修改 Blender 的语言文件、节点标签或接口标签。
- 1.4.4 将 macOS 搜索框中的纯英文和未上屏拼音下移两个缩放单位，中文位置不变；复用已完成的节点索引，减少打开搜索框时的准备开销。更新后会重建一次缓存，之后的首次与重复打开可复用缓存；收藏、使用权重和设置保持不变。测试方法与耗时见[性能验证](PERFORMANCE.md)。
- 1.2.2 优化搜索匹配与索引准备。Blender 5.2.2 实测搜索核心中位耗时降低约 54%–59%，两版 Blender 共 10,935 次查询对照保持原有结果与排序；详见[性能验证](PERFORMANCE.md)。
- 1.2.1 修正着色器、脚本、部分几何与输出节点及 Split Toning 资产的颜色标签；Shader 类组合点也使用专用着色器绿色。节点仍按当前版本的真实注册类型与创建能力生成索引，不会在旧版中展示不存在的新节点。
- 中文名优先读取当前 Blender 的官方简中词典及翻译上下文，不切换你的界面语言；人工搜索别名单独记录。英文、中文、全拼和完整首字母均可检索，例如 `Mesh Bevel`、`网格倒角`、`wanggedaojiao`、`wgdj`。
- 升级 Blender 后，可用「刷新资产索引」发现新版自带的资产节点组。只索引本地可读取的 `.blend` 资产，不会把未下载的在线资产当作可直接添加的节点。
- 节点支持、译名处理与配色修正的版本变化见[变更日志](CHANGELOG.md)。
