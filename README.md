# Node Console

<img width="1920" height="600" alt="节点控制台 02" src="https://github.com/user-attachments/assets/c0468802-5677-4372-92f9-28a31d0f6dd7" />

![Blender](https://img.shields.io/badge/Blender-5.1.2%20%7C%205.2.2%20LTS-f5792a?logo=blender&logoColor=white)
![Version](https://img.shields.io/badge/version-1.5.5-blue)
![Category](https://img.shields.io/badge/category-Node%20Editor-555)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

作者：Anthem  
版本：1.5.5

[下载 / Download](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.5) · [版本记录 / Releases](https://github.com/AnthemZhou/Node_Console/releases) · [Issues](https://github.com/AnthemZhou/Node_Console/issues)

## Languages / 语言

<details>
<summary>English</summary>

Node Console replaces `Shift + A` in Blender's Geometry, Shader and Compositor node editors with a compact search panel. Find nodes in your preferred language, keep common nodes close at hand, and reuse node arrangements as Snippet Nodes.

### Features

- English-only or bilingual search with Chinese, Japanese, Korean, Russian or Spanish; Chinese mode also supports pinyin and initials.
- System Chinese input in the custom search field on macOS and Windows, with results updating after text is committed.
- Favorites that prioritize relevant results, plus draggable shortcut rows for frequently used nodes.
- Category colors shown as blocks or slim lines to help identify node types.
- Searchable local Asset Library node groups and manual asset-index refresh.
- Reusable Snippet Nodes with frames and internal connections, stored in an external JSON library.
- In-app version selection and updates, with optional Beta releases and local backups.

### Install

1. Download [Node_Console_1.5.5.zip](https://github.com/AnthemZhou/Node_Console/releases/download/v1.5.5/Node_Console_1.5.5.zip), not GitHub's automatically generated Source code archives.
2. Open Blender's `Edit > Preferences > Add-ons` and choose installation from disk.
3. Select the ZIP and enable `Node Console`.

### Search and Place

1. Open a Geometry, Shader or Compositor node editor and press `Shift + A`.
2. Type a node name, such as `noise` or `instance`. In Chinese mode, you can also enter `噪波`, `zaobo` or initials.
3. Press Enter or click a result, move the mouse to choose its position, then click or press Enter to place it.
4. Right-click a result to add or remove favorites and shortcuts.

An empty query shows shortcut nodes as vertical rows. Drag a row to reorder it and release to save; Escape, right-click or dropping outside cancels. Each editor keeps its own shortcut order. The three small lines at the right of a row indicate that it can be dragged.

### Input and Languages

Set `Node Language` to `English` for English-only search, or choose a second language to search both it and English. `Search Result Display` controls single-language or bilingual names. Fresh installs follow Blender's interface language; saved choices are retained. These settings do not change Blender's UI or your custom node names.

On macOS and Windows, use your Chinese input method directly in the search field. While composing or choosing candidates, the result list stays unchanged. Confirm the text to update search, then press Enter again to create a node. Escape first cancels composition without closing search. Direct English and pinyin input still searches as you type.

- Chinese: `Mesh Bevel`, `网格倒角`, `wanggedaojiao` and `wgdj` can find the same node. Full pinyin accepts syllable spaces and case variants; homophones and short queries can produce additional results.
- Japanese: hiragana/katakana and full-/half-width forms match, such as `のいず` and `ﾉｲｽﾞ` for `ノイズテクスチャ`. Kanji-reading inference and romaji-to-kanji conversion are not included.
- Korean: supports omitted spaces, initial consonants and committed partial forms, such as `노이즈텍`, `ㄴㅇㅈ` and `노ㅇ` for `노이즈 텍스처`. Unconfirmed IME composition is not searched.
- Russian: case-insensitive matching with equivalent `е/ё`. Spanish: accents may be omitted, while `n/ñ` remain distinct.

Node names use Blender's official translations, falling back to English where needed. Search follows native menu ordering where possible, with favorites and extra language matches as intentional enhancements. Settings and action text remain primarily English/Chinese.

### Snippet Nodes

1. Select the nodes or frame you want to reuse.
2. Press `Ctrl + Shift + G` (`Command + Shift + G` on macOS).
3. Enter a name and choose a category. If there is no enclosing frame, the snippet is saved with one.
4. Open search with `Shift + A`, then press the backtick key above Tab (`` ` ``) to enter Snippet Node mode. The `·` character from a Chinese input method also works.
5. Search by name, or pinyin in Chinese mode, then press Enter or click to insert the framed node set with its internal links.
6. Press `` ` `` or `·` again to return to normal search without clearing your query.

Right-click a snippet result to favorite it or delete it. Favorites appear first when entering Snippet Node mode. Preferences provide an expandable snippet list and the library path. Use the file browser to choose the active JSON library; clearing the path returns to the default library without deleting files.

`None` means no category was assigned. Choose an editor-appropriate category in the save dialog; linked selections infer one from a terminal node, while unlinked selections default to None. Saved categories cannot currently be edited directly in Preferences.

### Preferences

- **Language and display:** node language, single/bilingual names, and category color blocks, lines or no color decoration.
- **Panel size:** overall scale and width; dragging the panel's right edge also adjusts its width.
- **Assets:** show cached Asset Library node groups and use `Refresh Asset Index` after changing libraries or upgrading Blender. Only locally readable assets are indexed.
- **Shortcuts:** customize the keys and modifiers for opening search and saving Snippet Nodes separately.
- **Favorites and libraries:** manage favorites, shortcut order, saved snippets and the active library path.

### Online Updates

1. Enable `Allow Online Access` in Blender's system preferences.
2. Click `Update` in Node Console Preferences to check available releases.
3. Choose a version and review its short update description, then click the download icon and confirm installation.

The list shows the three newest eligible versions. `Other Versions` opens GitHub Releases. Beta releases are hidden unless you enable Beta and check again; changing the checkbox does not install anything.

Updates keep a local backup and preserve settings, favorites, shortcuts and snippet files. They activate after any search, placement or naming operation finishes, without restarting Blender or resetting other add-ons' shortcuts. If activation fails, the updater attempts to restore the previous version. Source checkouts cannot be replaced through this updater.

### Compatibility

- Tested Blender versions: 5.1.2 and 5.2.2 LTS. Available nodes depend on the running Blender version and editor.
- Chinese IME input has been used on Apple Silicon macOS and Windows. Real Japanese/Korean IMEs, Intel Macs, third-party IMEs and all display/keyboard configurations are not fully verified.
- Linux supports direct English/pinyin input and pasted text; native IME integration is not provided. If native input cannot initialize, the standard input path remains available.
- The add-on does not modify Blender's language files, node labels or socket labels.

Version details are in [Releases](https://github.com/AnthemZhou/Node_Console/releases) and the [changelog](CHANGELOG.md). Technical measurements and verification limits are in [PERFORMANCE.md](PERFORMANCE.md).

</details>

<details>
<summary>日本語</summary>

Node Console は Blender のノード検索アドオンです。ジオメトリ、シェーダー、コンポジターの各エディターで、多言語検索、お気に入り、並べ替え可能なショートカット、再利用できるノードの組み合わせを使えます。

### インストールと言語設定

1. [リリースページ](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.5)から `Node_Console_1.5.5.zip` をダウンロードし、Blender の環境設定からインストールして有効にします。Source code ZIP は使いません。
2. `Node Language` を `日本語` にします。`Search Result Display` で英語のみ、日本語のみ、または両方の表示順を選べます。英語だけで検索・表示したい場合は `Node Language` を `English` にします。

### 検索と操作

- ノードエディターで `Shift + A` を押します。英語は常に検索でき、日本語ではひらがな・カタカナ、全角・半角を同一視します。`のいず` と `ﾉｲｽﾞ` は `ノイズテクスチャ` に一致します。漢字の読みの推測やローマ字から漢字への変換辞書は含まれません。
- IME の未確定文字や候補を変更している間は結果を維持し、文字の確定後に検索を更新します。英語の直接入力はリアルタイム検索です。
- Enter またはクリックでノードを作成し、マウスで位置を決めてクリックまたは Enter で配置します。
- 結果を右クリックしてお気に入りやショートカットを登録します。検索欄が空のときのショートカット行はドラッグで並べ替えでき、順序はエディターごとに保存されます。
- 設定では検索欄の大きさ、幅、カテゴリの色表示、各ショートカットを変更できます。アセットライブラリを変更したら `Refresh Asset Index` で更新します。

### スニペットと更新

選択したノードやフレームを `Ctrl + Shift + G`（macOS は `Command + Shift + G`）で名前・カテゴリ付きのスニペットとして保存します。検索欄でバッククォートキー（Tab の上のキー）または `·` を押すと、入力を保持したまま通常検索とスニペット検索を切り替えます。ライブラリは外部 JSON ファイルに保存され、設定から場所や項目を確認できます。結果の右クリックでお気に入りへの登録や削除ができます。

設定の更新ボタンで GitHub のリリースを確認し、バージョンを選んでインストールを確定します。Beta は任意で、初期状態では無効です。更新前にバックアップを保持し、お気に入りやライブラリを消去しません。

### 注意事項

動作確認済みの Blender は 5.1.2 / 5.2.2 LTS です。ノード名は公式翻訳を使い、未翻訳の名前は英語で表示します。設定画面やメッセージは主に英語・中国語です。日本語・韓国語の実際のシステム IME や全キーボード配置は、Mac/Windows での実機検証がまだ必要です。

バージョンごとの変更は [Releases](https://github.com/AnthemZhou/Node_Console/releases) と[変更履歴](CHANGELOG.md)、詳しい検証範囲は [PERFORMANCE.md](PERFORMANCE.md) を参照してください。

</details>

<details>
<summary>한국어</summary>

Node Console은 Blender의 지오메트리, 셰이더, 컴포지터 노드 편집기를 위한 검색 애드온입니다. 다국어 검색, 즐겨찾기, 드래그로 정렬하는 바로가기, 재사용 가능한 노드 묶음을 제공합니다.

### 설치와 언어 설정

1. [릴리스 페이지](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.5)에서 `Node_Console_1.5.5.zip`을 받아 Blender 환경설정에서 설치하고 활성화합니다. Source code ZIP은 사용하지 않습니다.
2. `Node Language`를 `한국어`로 선택합니다. `Search Result Display`에서 영어만, 한국어만 또는 두 언어의 표시 순서를 선택할 수 있습니다. 영어로만 검색하고 표시하려면 `Node Language`를 `English`로 선택합니다.

### 검색과 조작

- 노드 편집기에서 `Shift + A`를 누릅니다. 영어는 항상 검색할 수 있으며, 한국어는 띄어쓰기 생략, 초성, 확정된 불완전 음절 형태를 지원합니다. `노이즈텍`, `ㄴㅇㅈ`, `노ㅇ`으로 `노이즈 텍스처`를 찾을 수 있습니다.
- IME로 글자를 조합하거나 후보를 바꾸는 동안에는 검색 결과를 유지합니다. 입력이 확정된 부분만 검색에 반영하며, 아직 조합 중인 다음 글자는 포함하지 않습니다. 영어 직접 입력은 실시간으로 검색합니다.
- Enter 또는 결과 클릭으로 노드를 생성하고, 마우스로 위치를 정한 뒤 클릭 또는 Enter로 배치합니다.
- 결과를 우클릭해 즐겨찾기나 바로가기를 추가합니다. 검색어가 없을 때 나타나는 바로가기 행은 드래그로 정렬하며, 순서는 편집기별로 저장됩니다.
- 환경설정에서 검색창 크기와 너비, 범주 색상, 각 단축키를 바꿀 수 있습니다. 에셋 라이브러리를 변경하면 `Refresh Asset Index`로 갱신합니다.

### 스니펫과 업데이트

노드나 프레임을 선택하고 `Ctrl + Shift + G`(macOS: `Command + Shift + G`)를 눌러 이름과 범주를 지정한 스니펫으로 저장합니다. 검색창에서 백틱 키(Tab 위의 키) 또는 `·`를 누르면 검색어를 유지하면서 일반 검색과 스니펫 검색을 전환합니다. 라이브러리는 외부 JSON 파일에 저장되며, 환경설정에서 경로와 항목을 확인할 수 있습니다. 결과를 우클릭해 즐겨찾기에 추가하거나 삭제할 수 있습니다.

환경설정의 업데이트 버튼으로 GitHub 릴리스를 확인하고 버전을 선택한 뒤 설치를 확정합니다. Beta는 선택 사항이며 기본값은 꺼짐입니다. 업데이트 전 백업을 보관하고 즐겨찾기와 라이브러리를 유지합니다.

### 참고 사항

검증한 Blender 버전은 5.1.2 / 5.2.2 LTS입니다. 노드 이름은 공식 번역을 사용하며, 번역이 없으면 영어로 표시합니다. 설정과 메시지는 주로 영어·중국어입니다. 한국어·일본어 시스템 IME와 모든 키보드 배열은 Mac/Windows 실기기 검증이 더 필요합니다.

버전별 변경 내용은 [Releases](https://github.com/AnthemZhou/Node_Console/releases)와 [변경 기록](CHANGELOG.md), 상세 검증 범위는 [PERFORMANCE.md](PERFORMANCE.md)를 참고하세요.

</details>

<details>
<summary>Русский</summary>

Node Console помогает искать и добавлять узлы в редакторах геометрических узлов, шейдеров и композитинга Blender. Дополнение поддерживает несколько языков, избранное, перетаскиваемые строки быстрого доступа и повторно используемые наборы узлов.

### Установка и язык

1. Скачайте `Node_Console_1.5.5.zip` со [страницы релиза](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.5), установите через настройки Blender и включите Node Console. Не используйте архив Source code.
2. В `Node Language` выберите `Русский`. Параметр `Search Result Display` задаёт английские, русские или двуязычные названия и их порядок. Для поиска только на английском выберите `English` в `Node Language`.

### Поиск и работа с узлами

- Нажмите `Shift + A` в редакторе узлов. Английские названия доступны всегда. Русский поиск не зависит от регистра и считает `е` и `ё` эквивалентными: `объем` находит названия с `Объём`. Мягкий и твёрдый знаки не удаляются.
- Нажмите Enter или щёлкните по результату, затем выберите положение мышью и подтвердите щелчком или Enter.
- Через контекстное меню добавляйте узлы в избранное или список быстрого доступа. При пустом запросе строки быстрого доступа можно перетаскивать; каждый редактор хранит свой порядок.
- В настройках можно менять размер и ширину поиска, цвета категорий и сочетания клавиш. После изменения библиотек ресурсов используйте `Refresh Asset Index`.
- При использовании IME результаты меняются после подтверждения текста, а не при выборе кандидата. Обычный ввод обновляет поиск сразу.

### Наборы узлов и обновления

Выберите узлы или рамку и нажмите `Ctrl + Shift + G` (macOS: `Command + Shift + G`), чтобы сохранить Snippet Node с именем и категорией. Клавиша обратной кавычки над Tab или `·` переключает обычный поиск и поиск наборов, сохраняя запрос. Библиотека хранится во внешнем JSON-файле; путь и сохранённые наборы доступны в настройках. Контекстное меню результата позволяет добавить набор в избранное или удалить его.

Кнопка обновления проверяет релизы GitHub. Выберите версию и подтвердите установку. Beta-версии включаются отдельно и по умолчанию скрыты. Перед заменой сохраняется резервная копия; избранное и библиотеки не очищаются.

### Ограничения

Проверены Blender 5.1.2 и 5.2.2 LTS. Названия используют официальный перевод Blender с возвратом к английскому при его отсутствии. Настройки и сообщения преимущественно на английском и китайском. Не все системные IME, клавиатуры и окна кандидатов на Mac/Windows проверены на реальном оборудовании, особенно для японского и корейского.

Изменения версий: [Releases](https://github.com/AnthemZhou/Node_Console/releases) и [история изменений](CHANGELOG.md). Подробности проверок: [PERFORMANCE.md](PERFORMANCE.md).

</details>

<details>
<summary>Español</summary>

Node Console facilita la búsqueda y creación de nodos en los editores de geometría, sombreado y composición de Blender. Ofrece búsqueda multilingüe, favoritos, accesos rápidos que puedes ordenar arrastrando y conjuntos de nodos reutilizables.

### Instalación e idioma

1. Descarga `Node_Console_1.5.5.zip` desde la [página de la versión](https://github.com/AnthemZhou/Node_Console/releases/tag/v1.5.5), instálalo desde las preferencias de Blender y activa Node Console. No uses los archivos Source code.
2. Selecciona `Español` en `Node Language`. `Search Result Display` permite mostrar inglés, español o ambos idiomas en el orden que prefieras. Para buscar solo en inglés, selecciona `English` en `Node Language`.

### Búsqueda y uso

- Pulsa `Shift + A` en un editor de nodos. El inglés siempre está disponible. La búsqueda en español admite mayúsculas, minúsculas y palabras sin tildes: `posicion` encuentra `Posición`. Se distingue entre `n` y `ñ`.
- Pulsa Enter o haz clic en un resultado para crear el nodo; mueve el ratón y confirma su posición con un clic o Enter.
- Haz clic derecho para añadir favoritos o accesos rápidos. Con la búsqueda vacía, puedes ordenar los accesos rápidos arrastrando sus filas. Cada editor mantiene su propio orden.
- En las preferencias puedes ajustar tamaño, anchura, colores de categoría y atajos. Usa `Refresh Asset Index` después de cambiar las bibliotecas de recursos.
- Al utilizar un IME, los resultados se actualizan al confirmar el texto, no al elegir candidatos. La escritura directa sigue buscando en tiempo real.

### Conjuntos de nodos y actualizaciones

Selecciona nodos o un marco y pulsa `Ctrl + Shift + G` (macOS: `Command + Shift + G`) para guardar un Snippet Node con nombre y categoría. La tecla de acento grave situada sobre Tab, o `·`, alterna entre nodos normales y conjuntos guardados sin borrar la búsqueda. La biblioteca se guarda en un JSON externo; puedes consultar su ruta y los elementos en las preferencias. Haz clic derecho en un resultado para añadirlo a favoritos o eliminarlo.

El botón de actualización consulta las versiones de GitHub. Selecciona una versión y confirma la instalación. Las versiones Beta son opcionales y están desactivadas por defecto. Se conserva una copia de seguridad antes de sustituir el complemento, sin borrar favoritos ni bibliotecas.

### Compatibilidad

Versiones de Blender comprobadas: 5.1.2 y 5.2.2 LTS. Se usan traducciones oficiales con nombres en inglés cuando faltan traducciones. Los ajustes y mensajes siguen principalmente en inglés y chino. No se han verificado todos los métodos de entrada, teclados y candidatos en equipos Mac/Windows reales, especialmente los IME japonés y coreano.

Cambios por versión: [Releases](https://github.com/AnthemZhou/Node_Console/releases) y [registro de cambios](CHANGELOG.md). Pruebas y limitaciones: [PERFORMANCE.md](PERFORMANCE.md).

</details>

## 中文

Node Console 是一个 Blender 节点搜索增强插件。在几何、材质和合成节点编辑器中，用紧凑的搜索框替代 `Shift + A` 的默认添加入口，更快找到节点、调用常用节点，并复用自己的节点组合。

### 功能

- **多语言搜索**：支持英文单语，或英文与中文、日语、韩语、俄语、西班牙语双语检索；中文模式支持全拼和首字母。
- **中文输入法**：macOS 和 Windows 可直接在搜索框内输入中文，确认上屏后再更新结果。
- **收藏与快捷节点**：优先显示相关收藏；空搜索时展示常用节点，可拖动排序。
- **类目颜色**：用颜色底块或细线区分节点类型，方便扫描结果。
- **资产节点**：检索本地资产库中的节点组，支持手动刷新索引。
- **组合点**：将带 Frame 和内部连线的节点组合保存到外部 JSON 库，跨项目重复使用。
- **在线更新**：在偏好设置中选择版本、确认安装，可选加入 Beta 测试，并保留本地备份。

### 安装

1. 下载 [Node_Console_1.5.5.zip](https://github.com/AnthemZhou/Node_Console/releases/download/v1.5.5/Node_Console_1.5.5.zip)，不要使用 GitHub 自动生成的 Source code 压缩包。
2. 打开 Blender 的 `编辑 > 偏好设置 > 插件`，选择从磁盘安装。
3. 选择 ZIP 文件并启用 `Node Console`。

### 搜索与放置

1. 打开几何、材质或合成节点编辑器，按 `Shift + A`。
2. 输入节点名，例如 `noise`、`instance`；中文模式下也可以输入「噪波」、`zaobo` 或首字母。
3. 按 Enter 或点击结果，移动鼠标确定位置，再点击或按 Enter 放置节点。
4. 右键结果，可以添加或取消收藏、管理快捷节点。

空搜索时会显示纵向快捷节点列表。按住整行拖动，松开保存顺序；按 Esc、右键或拖到列表外松开可取消。几何、材质、合成编辑器分别保存自己的快捷节点顺序。行尾的三条浅色横线表示可拖动。

### 输入与语言

在偏好设置的「节点语言」中选择 `English`，即可只用英文检索和显示；选择其他语言时，该语言与英文都可搜索。「搜索结果显示」控制单语或双语名称及前后顺序。首次安装默认跟随 Blender 界面语言，已有选择会保留，不改变 Blender 自身的语言或用户自定义节点名称。

macOS 和 Windows 用户可以直接使用中文输入法。组词时显示带下划线的拼音，候选词由系统提供；选择候选词期间结果列表保持不变，确认文字上屏后才搜索。组词时按 Enter 只确认候选词，再按 Enter 才创建节点；Esc 先取消组词而不关闭搜索框。直接输入英文或拼音时仍实时检索。

- **中文**：`Mesh Bevel`、「网格倒角」、`wanggedaojiao`、`wgdj` 都能找到对应节点。完整拼音支持大小写和音节间空格；同音词与短输入可能包含更多候选。
- **日语**：支持平假名、片假名、全角和半角互搜，例如 `のいず`、`ﾉｲｽﾞ` 匹配 `ノイズテクスチャ`；不推测汉字读音，也不内置罗马音转汉字词典。
- **韩语**：支持省略空格、声母和已提交的部分拼写，例如 `노이즈텍`、`ㄴㅇㅈ`、`노ㅇ` 匹配 `노이즈 텍스처`；仍在输入法中组字的内容不会触发检索。
- **俄语与西班牙语**：俄语支持大小写和 `е/ё` 等价搜索；西语可省略重音，但区分 `n/ñ`。

节点名使用当前 Blender 的官方翻译，缺译时回退英文。排序尽量接近原生搜索，同时保留收藏和额外语言匹配等增强，因此不保证所有查询与原生列表完全相同。插件设置和操作提示目前主要为中英界面。

### 组合点

1. 选中需要复用的节点或 Frame。
2. 按 `Ctrl + Shift + G`；macOS 默认使用 `Command + Shift + G`。
3. 输入名称并选择类目。没有外层 Frame 时，保存的组合点会包含自动创建的 Frame。
4. 按 `Shift + A` 打开搜索，再按 Tab 上方的反引号键 `` ` `` 进入「组合点」模式；中文输入法产生的 `·` 也有效。
5. 按名称搜索，中文模式也支持拼音；按 Enter 或点击结果，插入带 Frame 和内部连线的节点组合。
6. 再按 `` ` `` 或 `·` 返回普通节点搜索，当前输入不会清空。

右键组合点结果可以收藏或删除；进入组合点模式时，收藏项会优先显示。偏好设置中可展开组合点列表，并查看外部 JSON 库路径。下方文件浏览入口用于选择当前库；清空路径可回到默认库，不会删除文件。

标签中的「无」表示未指定类目，并非报错。保存时可在弹窗中选择当前编辑器适用的类目；有内部连线时会从末端节点推断默认类目，无连线时默认为「无」。目前尚不能直接在偏好设置中编辑已保存条目的类目。

### 偏好设置

- **语言与显示**：选择节点语言、单语或双语顺序，以及颜色底块、颜色竖线或关闭类目颜色。
- **窗口大小**：调整搜索框的整体大小和宽度，也可以拖动搜索框右侧边缘改变宽度。
- **缓存资产**：「显示用户自定义的缓存资产节点」控制资产结果显示；更改资产库或升级 Blender 后，使用「刷新资产索引」。只索引本地可读取的资产。
- **快捷键**：分别设置打开搜索框、保存组合点的按键和修饰键。
- **收藏与库管理**：管理收藏、快捷节点顺序、已保存的组合点和当前库文件路径。

### 在线更新

1. 在 Blender 的 `偏好设置 > 系统` 中允许在线访问。
2. 点击 Node Console 偏好设置中的「更新」，检查可用版本。
3. 在下拉菜单中选择版本并查看简短更新说明，点击下载图标，确认后安装。

列表显示最近三个符合条件的版本；「其他版本」打开 GitHub Releases。Beta 默认关闭，勾选后重新检查才会包含测试版，勾选本身不会安装或降级。

更新前保留本地备份，并保留设置、收藏、快捷节点和组合点库。搜索、节点放置或命名操作结束后自动热加载，无需重启 Blender，不重置其他插件的快捷键。启用失败时会尝试恢复原版本。Git 源码工程不通过此按钮替换。

### 兼容与说明

- 已测试的 Blender 版本为 5.1.2 和 5.2.2 LTS；可用节点随当前 Blender 版本与编辑器而定。
- 中文输入已有 Apple Silicon macOS 和 Windows 使用验证；日韩真实输入法、Intel Mac、第三方输入法以及所有显示和键盘配置尚未完整验证。
- Linux 支持英文、拼音直接输入及粘贴文本，暂未提供原生输入法集成；原生输入模块初始化失败时会保留普通输入路径。
- 插件不会修改 Blender 的语言文件、节点标签或插口标签。

各版本变化请查看 [Release](https://github.com/AnthemZhou/Node_Console/releases) 和[变更日志](CHANGELOG.md)；测试数据与验证边界见[技术验证说明](PERFORMANCE.md)。
