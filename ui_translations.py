"""Node Console UI copy, independent of node-search language and Blender catalogs.

Translations below are add-on editorial copy, not official Blender node names.
Use a private RNA context so common words never override Blender or other add-ons.
"""

CONTEXT = 'NodeConsole'
ADDON_DESCRIPTION = 'Language-independent custom node launcher with favorite boosting.'
LANGUAGES = ('ja', 'ko', 'ru', 'es')
LOCALES = {'zh_HANS': 'zh', 'zh_CN': 'zh', 'ja_JP': 'ja', 'ja': 'ja',
           'ko_KR': 'ko', 'ko': 'ko', 'ru_RU': 'ru', 'ru': 'ru', 'es': 'es', 'es_ES': 'es'}

# Rows are Japanese, Korean, Russian, Spanish; English is the source key.
ROWS = {
    'Search nodes...': ('ノードを検索...', '노드 검색...', 'Поиск узлов...', 'Buscar nodos...'),
    'No results found': ('結果がありません', '검색 결과 없음', 'Ничего не найдено', 'Sin resultados'),
    'Add Favorite': ('お気に入りに追加', '즐겨찾기 추가', 'В избранное', 'Añadir a favoritos'),
    'Remove Favorite': ('お気に入りから削除', '즐겨찾기 제거', 'Убрать из избранного', 'Quitar de favoritos'),
    'Add Shortcut': ('クイックノードに追加', '빠른 노드 추가', 'В быстрые узлы', 'Añadir a acceso rápido'),
    'Remove Shortcut': ('クイックノードから削除', '빠른 노드 제거', 'Убрать из быстрых узлов', 'Quitar de acceso rápido'),
    'Search Result Display': ('検索結果の表示', '검색 결과 표시', 'Показ имён', 'Mostrar nombres'),
    'Node Language': ('ノードの言語', '노드 언어', 'Язык узлов', 'Idioma de nodos'),
    'Enable Chinese Fuzzy Match': ('中国語のあいまい検索', '중국어 유사 검색', 'Нечёткий поиск на китайском', 'Búsqueda flexible en chino'),
    'May slightly slow live search': ('検索が少し遅くなる場合があります', '검색 속도가 약간 느려질 수 있습니다', 'Может немного замедлить поиск', 'Puede ralentizar ligeramente la búsqueda'),
    'Show Cached Asset Nodes': ('ユーザーアセットのキャッシュを表示', '사용자 에셋 노드 캐시 표시', 'Кэш пользовательских ассетов', 'Mostrar caché de recursos propios'),
    'Category Color Display': ('カテゴリの色表示', '범주 색상 표시', 'Цвет категорий', 'Color de categorías'),
    'Color Line': ('カラーライン', '색상 선', 'Цветная линия', 'Línea de color'),
    'Color Block': ('カラー背景', '색상 배경', 'Цветной фон', 'Fondo de color'),
    'Off': ('オフ', '끄기', 'Выкл.', 'Desactivado'),
    'Cached Assets': ('キャッシュ済みアセット', '캐시된 에셋', 'Ассеты в кэше', 'Recursos en caché'),
    'Console Size': ('検索画面のサイズ', '검색 창 크기', 'Масштаб поиска', 'Escala del buscador'),
    'Console Width': ('検索画面の幅', '검색 창 너비', 'Ширина поиска', 'Ancho del buscador'),
    'Reset Width': ('幅をリセット', '너비 초기화', 'Сбросить ширину', 'Restablecer ancho'),
    'Reset Size': ('サイズをリセット', '크기 초기화', 'Сбросить масштаб', 'Restablecer escala'),
    'Shortcut conflict': ('ショートカットの競合', '단축키 충돌', 'Конфликт клавиш', 'Conflicto de atajos'),
    'Current shortcut temporarily overrides': ('現在のキーが一時的に優先されます', '현재 단축키가 임시로 우선 적용됩니다', 'Текущее сочетание временно заменяет', 'El atajo actual sustituye temporalmente a'),
    'Original shortcut restores after Node Console uses a non-conflicting shortcut.': ('競合しないキーに変更すると元のショートカットが復元されます。', '충돌하지 않는 단축키로 변경하면 기존 단축키가 복원됩니다.', 'Исходное сочетание восстановится после выбора свободных клавиш для Node Console.', 'El atajo original se restaura al elegir uno sin conflictos para Node Console.'),
    'Refresh Asset Index': ('アセット索引を更新', '에셋 색인 갱신', 'Обновить индекс', 'Actualizar índice'),
    'Shortcut': ('ショートカット', '단축키', 'Сочетание клавиш', 'Atajo'),
    'Command': ('Command', 'Command', 'Command', 'Command'),
    'Favorites': ('お気に入り', '즐겨찾기', 'Избранное', 'Favoritos'),
    'No favorite nodes': ('お気に入りのノードはありません', '즐겨찾기 노드 없음', 'Нет избранных узлов', 'No hay nodos favoritos'),
    'Shortcuts': ('クイックノード', '빠른 노드', 'Быстрые узлы', 'Nodos de acceso rápido'),
    'No node shortcuts': ('クイックノードはありません', '빠른 노드 없음', 'Нет быстрых узлов', 'No hay nodos de acceso rápido'),
    'Could not save shortcut; settings were not changed': ('クイックノードを保存できません。設定は変更されていません', '빠른 노드를 저장하지 못했습니다. 설정은 변경되지 않았습니다', 'Не удалось сохранить быстрый узел; настройки не изменены', 'No se pudo guardar el acceso rápido; los ajustes no cambiaron'),
    'Geometry Nodes': ('ジオメトリノード', '지오메트리 노드', 'Геометрические узлы', 'Nodos de geometría'),
    'Shader Nodes': ('シェーダーノード', '셰이더 노드', 'Шейдерные узлы', 'Nodos de sombreado'),
    'Compositor Nodes': ('コンポジターノード', '컴포지터 노드', 'Узлы композитинга', 'Nodos de composición'),
    'Uncategorized': ('未分類', '미분류', 'Без категории', 'Sin categoría'),
    'Name': ('名前', '이름', 'Имя', 'Nombre'),
    'Category': ('カテゴリ', '범주', 'Категория', 'Categoría'),
    'Snippet Node': ('スニペット', '스니펫', 'Сниппет', 'Fragmento'),
    'Snippet Nodes': ('スニペット', '스니펫', 'Сниппеты', 'Fragmentos'),
    'No snippet nodes': ('スニペットはありません', '스니펫 없음', 'Нет сниппетов', 'No hay fragmentos'),
    'Save Snippet Node': ('スニペットを保存', '스니펫 저장', 'Сохранить сниппет', 'Guardar fragmento'),
    'Remove Snippet Node': ('スニペットを削除', '스니펫 삭제', 'Удалить сниппет', 'Eliminar fragmento'),
    'Snippet Node Name': ('スニペット名', '스니펫 이름', 'Имя сниппета', 'Nombre del fragmento'),
    'Snippet Node Category': ('スニペットのカテゴリ', '스니펫 범주', 'Категория сниппета', 'Categoría del fragmento'),
    'nodes': ('ノード', '노드', 'узлов', 'nodos'),
    'links': ('リンク', '연결', 'связей', 'conexiones'),
    'Open Search Shortcut': ('検索を開くキー', '검색 열기 단축키', 'Открыть поиск', 'Atajo para abrir búsqueda'),
    'Save Snippet Node Shortcut': ('スニペットを保存するキー', '스니펫 저장 단축키', 'Сохранить сниппет', 'Atajo para guardar fragmento'),
    'Snippet Library File': ('スニペットライブラリのファイル', '스니펫 라이브러리 파일', 'Файл библиотеки сниппетов', 'Archivo de biblioteca de fragmentos'),
    'Snippet Libraries': ('スニペットライブラリ', '스니펫 라이브러리', 'Библиотеки сниппетов', 'Bibliotecas de fragmentos'),
    'Default Library': ('既定のライブラリ', '기본 라이브러리', 'Библиотека по умолчанию', 'Biblioteca predeterminada'),
    'Active': ('有効', '활성', 'Активна', 'Activa'),
    'Name is required': ('名前を入力してください', '이름을 입력하세요', 'Укажите имя', 'Es necesario un nombre'),
    'Select nodes to save as a snippet': ('保存するノードを選択してください', '스니펫으로 저장할 노드를 선택하세요', 'Выберите узлы для сниппета', 'Selecciona los nodos que guardar como fragmento'),
    'This snippet already exists': ('このスニペットは保存済みです', '이미 저장된 스니펫입니다', 'Этот сниппет уже существует', 'Este fragmento ya existe'),
    'Could not save snippet library': ('スニペットライブラリを保存できません', '스니펫 라이브러리를 저장하지 못했습니다', 'Не удалось сохранить библиотеку сниппетов', 'No se pudo guardar la biblioteca de fragmentos'),
    'Existing snippet': ('既存のスニペット', '기존 스니펫', 'Существующий сниппет', 'Fragmento existente'),
    'Input': ('入力', '입력', 'Ввод', 'Entrada'),
    'Output': ('出力', '출력', 'Вывод', 'Salida'),
    'Geometry': ('ジオメトリ', '지오메트리', 'Геометрия', 'Geometría'),
    'Shader': ('シェーダー', '셰이더', 'Шейдер', 'Sombreado'),
    'Color': ('カラー', '색상', 'Цвет', 'Color'),
    'Converter': ('変換', '변환', 'Преобразование', 'Conversión'),
    'Vector': ('ベクトル', '벡터', 'Вектор', 'Vector'),
    'Texture': ('テクスチャ', '텍스처', 'Текстура', 'Textura'),
    'Filter': ('フィルター', '필터', 'Фильтр', 'Filtro'),
    'Mask': ('マスク', '마스크', 'Маска', 'Máscara'),
    'Distort': ('変形', '왜곡', 'Искажение', 'Distorsión'),
    'Utility': ('ユーティリティ', '유틸리티', 'Служебные', 'Utilidades'),
    'Layout': ('レイアウト', '레이아웃', 'Макет', 'Disposición'),
    'None': ('なし', '없음', 'Нет', 'Ninguna'),
    'Update': ('更新', '업데이트', 'Обновить', 'Actualizar'),
    'Check for Updates': ('更新を確認', '업데이트 확인', 'Проверить обновления', 'Buscar actualizaciones'),
    'Accept Beta Versions': ('ベータ版を含める', '베타 버전 포함', 'Получать бета-версии', 'Incluir versiones beta'),
    'Install Selected Version': ('選択したバージョンをインストール', '선택한 버전 설치', 'Установить выбранную версию', 'Instalar versión seleccionada'),
    'Available Versions': ('利用可能なバージョン', '사용 가능한 버전', 'Доступные версии', 'Versiones disponibles'),
    'Other Versions': ('その他のバージョン', '다른 버전', 'Другие версии', 'Otras versiones'),
    'Open all releases on GitHub': ('GitHub ですべてのリリースを表示', 'GitHub에서 모든 릴리스 보기', 'Открыть все выпуски на GitHub', 'Ver todas las versiones en GitHub'),
    'Stable': ('安定版', '안정 버전', 'Стабильная', 'Estable'),
    'Current': ('現在のバージョン', '현재 버전', 'Текущая', 'Actual'),
    'Installed': ('インストール済み', '설치됨', 'Установлена', 'Instalada'),
    'Older Stable': ('旧安定版', '이전 안정 버전', 'Предыдущая стабильная', 'Estable anterior'),
    'See release notes': ('更新内容を参照', '릴리스 노트 참조', 'См. примечания к выпуску', 'Ver notas de la versión'),
    'Currently installed; check for updates to refresh the list': ('現在インストール済み。更新を確認すると一覧を更新します', '현재 설치된 버전입니다. 업데이트를 확인하면 목록이 갱신됩니다', 'Уже установлена; проверьте обновления, чтобы обновить список', 'Ya instalada; busca actualizaciones para renovar la lista'),
    'Check for updates first': ('先に更新を確認してください', '먼저 업데이트를 확인하세요', 'Сначала проверьте обновления', 'Busca actualizaciones primero'),
    'Select a version to install': ('インストールするバージョンを選択', '설치할 버전 선택', 'Выберите версию', 'Selecciona una versión'),
    'No compatible releases found': ('互換性のあるバージョンがありません', '호환되는 버전 없음', 'Нет совместимых версий', 'No hay versiones compatibles'),
    'Beta versions may be unstable': ('ベータ版は不安定な場合があります', '베타 버전은 불안정할 수 있습니다', 'Бета-версии могут быть нестабильны', 'Las versiones beta pueden ser inestables'),
    'This will install an older version': ('以前のバージョンに戻します', '이전 버전으로 되돌립니다', 'Будет установлена более старая версия', 'Se instalará una versión anterior'),
    'Older versions may restore the old update interface': ('以前の更新画面に戻る場合があります', '이전 업데이트 화면으로 돌아갈 수 있습니다', 'Старые версии могут вернуть прежний интерфейс обновления', 'Las versiones anteriores pueden restaurar la interfaz antigua de actualización'),
    'A local backup will be kept': ('ローカルにバックアップを保存します', '로컬 백업이 보관됩니다', 'Будет сохранена локальная резервная копия', 'Se conservará una copia de seguridad local'),
    'Release changed; check for updates again': ('リリース情報が変わりました。再確認してください', '릴리스 정보가 변경되었습니다. 업데이트를 다시 확인하세요', 'Выпуск изменился; проверьте обновления снова', 'La versión cambió; busca actualizaciones de nuevo'),
    'Selection changed; confirm the version again': ('選択が変わりました。バージョンを再確認してください', '선택이 변경되었습니다. 버전을 다시 확인하세요', 'Выбор изменился; подтвердите версию снова', 'La selección cambió; confirma la versión de nuevo'),
    'Install': ('インストール', '설치', 'Установить', 'Instalar'),
    'Checking GitHub...': ('GitHub を確認中...', 'GitHub 확인 중...', 'Проверка GitHub...', 'Consultando GitHub...'),
    'Downloading update...': ('更新をダウンロード中...', '업데이트 다운로드 중...', 'Загрузка обновления...', 'Descargando actualización...'),
    'Finish the current node operation to update': ('ノード操作の完了後に更新します', '현재 노드 작업이 끝나면 업데이트합니다', 'Завершите операцию с узлами для обновления', 'Termina la operación con nodos para actualizar'),
    'Activating update...': ('更新を適用中...', '업데이트 적용 중...', 'Активация обновления...', 'Activando actualización...'),
    'Updated and active': ('更新を適用しました', '업데이트 적용 완료', 'Обновление активно', 'Actualización activa'),
    'Update activation failed; previous version restored': ('適用に失敗しました。以前のバージョンに戻しました', '업데이트 적용 실패. 이전 버전을 복원했습니다', 'Активация не удалась; прежняя версия восстановлена', 'Falló la activación; se restauró la versión anterior'),
    'Could not restore the add-on; restart Blender and check the backup': ('復元できません。Blender を再起動しバックアップを確認してください', '복원하지 못했습니다. Blender를 재시작하고 백업을 확인하세요', 'Не удалось восстановить дополнение; перезапустите Blender и проверьте резервную копию', 'No se pudo restaurar el complemento; reinicia Blender y revisa la copia de seguridad'),
    'Already up to date': ('最新版です', '최신 버전입니다', 'Установлена последняя версия', 'Ya está actualizado'),
    'Restart Blender to activate': ('Blender を再起動すると有効になります', 'Blender를 재시작하면 적용됩니다', 'Перезапустите Blender для активации', 'Reinicia Blender para activar'),
    'Enable Allow Online Access in Blender Preferences > System': ('Blender のプリファレンス > システムでオンラインアクセスを許可してください', 'Blender 환경설정 > 시스템에서 온라인 접근을 허용하세요', 'Разрешите доступ к сети в настройках Blender > Система', 'Permite el acceso a Internet en Preferencias > Sistema de Blender'),
    'GitHub connection failed; try again later': ('GitHub に接続できません。後で再試行してください', 'GitHub 연결 실패. 나중에 다시 시도하세요', 'Не удалось подключиться к GitHub; повторите позже', 'No se pudo conectar con GitHub; inténtalo más tarde'),
    'GitHub request limit reached; try again later': ('GitHub のリクエスト上限に達しました。後で再試行してください', 'GitHub 요청 한도에 도달했습니다. 나중에 다시 시도하세요', 'Достигнут лимит запросов GitHub; повторите позже', 'Se alcanzó el límite de solicitudes de GitHub; inténtalo más tarde'),
    'No published release found': ('公開済みのリリースがありません', '공개된 릴리스 없음', 'Нет опубликованных выпусков', 'No hay versiones publicadas'),
    'Release has no matching installation ZIP': ('対応するインストール用 ZIP がありません', '해당 버전의 설치 ZIP이 없습니다', 'Нет подходящего установочного ZIP', 'La versión no incluye un ZIP de instalación compatible'),
    'Invalid release information': ('リリース情報が無効です', '잘못된 릴리스 정보', 'Некорректные сведения о выпуске', 'Información de versión no válida'),
    'Invalid installation package; nothing replaced': ('インストールパッケージが無効です。置換は行っていません', '설치 패키지가 잘못되었습니다. 파일은 교체되지 않았습니다', 'Некорректный пакет; файлы не заменены', 'Paquete no válido; no se sustituyó ningún archivo'),
    'This update requires a newer Blender': ('新しいバージョンの Blender が必要です', '더 최신 Blender 버전이 필요합니다', 'Для обновления нужен более новый Blender', 'Esta actualización requiere un Blender más reciente'),
    'Cannot update a source checkout; install the release ZIP first': ('ソース作業ツリーは更新できません。先にリリース ZIP をインストールしてください', '소스 작업 폴더는 업데이트할 수 없습니다. 먼저 릴리스 ZIP을 설치하세요', 'Нельзя обновить рабочую копию исходников; сначала установите ZIP выпуска', 'No se puede actualizar una copia de desarrollo; instala primero el ZIP publicado'),
    'Installation path is not safe to replace': ('このインストール先は安全に置換できません', '설치 경로를 안전하게 교체할 수 없습니다', 'Небезопасный путь для замены установки', 'La ruta de instalación no se puede reemplazar con seguridad'),
    'Cannot write the installation folder': ('インストール先に書き込めません', '설치 폴더에 쓸 수 없습니다', 'Нет доступа на запись в папку установки', 'No se puede escribir en la carpeta de instalación'),
    'Update conflicts with a custom data file': ('ユーザーデータと競合するため更新を中止しました', '사용자 데이터 파일과 충돌하여 업데이트를 중단했습니다', 'Обновление конфликтует с пользовательским файлом данных', 'La actualización entra en conflicto con un archivo de datos propio'),
    'Update failed; previous files retained': ('更新に失敗しました。以前のファイルを保持しました', '업데이트 실패. 기존 파일을 보존했습니다', 'Обновление не удалось; прежние файлы сохранены', 'Falló la actualización; se conservaron los archivos anteriores'),
    'Installed files changed; restart Blender before updating': ('インストール済みファイルが変わりました。更新前に Blender を再起動してください', '설치 파일이 변경되었습니다. 업데이트 전에 Blender를 재시작하세요', 'Установленные файлы изменились; перезапустите Blender перед обновлением', 'Los archivos instalados cambiaron; reinicia Blender antes de actualizar'),
}

ROWS.update({
    'Multilingual node search': ('多言語ノード検索', '다국어 노드 검색', 'Многоязычный поиск узлов', 'Búsqueda de nodos multilingüe'),
    'Preferences layout cleanup': ('設定画面の整理', '환경설정 레이아웃 정리', 'Улучшение макета настроек', 'Mejoras de diseño en preferencias'),
    'Chinese and pinyin ranking alignment': ('中国語とピンインの検索順を統一', '중국어와 병음 검색 순서 정렬', 'Согласование поиска на китайском и пиньине', 'Orden coherente entre chino y pinyin'),
    'English-only node search': ('英語のみのノード検索', '영어 전용 노드 검색', 'Поиск узлов только на английском', 'Búsqueda solo en inglés'),
    'Search after IME confirmation': ('IME 確定後に検索', '입력기 확정 후 검색', 'Поиск после подтверждения ввода', 'Búsqueda tras confirmar la entrada'),
    'Preferences display fixes': ('設定画面の表示修正', '환경설정 표시 수정', 'Исправления отображения настроек', 'Correcciones visuales en preferencias'),
    'Blender 5.3 node support': ('Blender 5.3 ノード対応', 'Blender 5.3 노드 지원', 'Поддержка узлов Blender 5.3', 'Compatibilidad con nodos de Blender 5.3'),
    'Online updates and shortcut sorting': ('オンライン更新とクイックノードの並べ替え', '온라인 업데이트와 빠른 노드 정렬', 'Онлайн-обновления и сортировка быстрых узлов', 'Actualización en línea y orden de accesos rápidos'),
    'Updates without restarting': ('再起動なしで更新', '재시작 없는 업데이트', 'Обновления без перезапуска', 'Actualizaciones sin reiniciar'),
    'Search caching and safer saves': ('検索キャッシュと安全な保存', '검색 캐시와 안전한 저장', 'Кэш поиска и надёжное сохранение', 'Caché de búsqueda y guardado seguro'),
    'Highlight the first search match': ('検索時に先頭の結果を選択', '검색 시 첫 결과 강조', 'Выделение первого результата поиска', 'Resaltar la primera coincidencia'),
    'Smoother shortcut dragging': ('クイックノードのドラッグ改善', '빠른 노드 드래그 개선', 'Плавное перетаскивание быстрых узлов', 'Arrastre más fluido de accesos rápidos'),
    'Mac Chinese input': ('Mac の中国語入力', 'Mac 중국어 입력', 'Ввод на китайском в macOS', 'Entrada de chino en Mac'),
    'Windows Chinese input and Beta updates': ('Windows の中国語入力とベータ版更新', 'Windows 중국어 입력 및 베타 업데이트', 'Ввод на китайском в Windows и бета-обновления', 'Entrada de chino en Windows y versiones beta'),
    'Compact version picker': ('バージョン選択の簡素化', '간결한 버전 선택', 'Компактный выбор версии', 'Selector de versiones compacto'),
    'Snippet categories and update layout': ('スニペット分類と更新画面', '스니펫 범주와 업데이트 레이아웃', 'Категории сниппетов и интерфейс обновлений', 'Categorías de fragmentos y diseño de actualización'),
    'Faster shortcut saving': ('クイックノードの保存を高速化', '빠른 노드 저장 속도 개선', 'Ускоренное сохранение быстрых узлов', 'Guardado más rápido de accesos rápidos'),
    'Faster first search': ('初回検索を高速化', '첫 검색 속도 개선', 'Ускорение первого поиска', 'Primera búsqueda más rápida'),
    'Search ranking and Chinese input speed': ('検索順と中国語入力の高速化', '검색 순서와 중국어 입력 속도 개선', 'Порядок поиска и скорость китайского ввода', 'Orden de resultados y rapidez del chino'),
    'Native search result alignment': ('標準検索との結果の整合', '기본 검색 결과와 정렬 일치', 'Согласование со встроенным поиском', 'Alineación con la búsqueda nativa'),
    'Faster opening and search input': ('起動と検索入力を高速化', '열기 및 검색 입력 속도 개선', 'Быстрое открытие и ввод поиска', 'Apertura y escritura más rápidas'),
})

# Additional RNA labels/tooltips: Chinese, Japanese, Korean, Russian, Spanish.
DETAILS = {
    'Preferences in six languages': ('偏好设置六语言完善', '設定画面の6言語対応', '환경설정 6개 언어 지원', 'Настройки на шести языках', 'Preferencias en seis idiomas'),
    ADDON_DESCRIPTION: ('支持多语言检索和收藏优先的自定义节点搜索面板。', '多言語検索とお気に入りの優先表示に対応したノード検索パネル。', '다국어 검색과 즐겨찾기 우선 표시를 지원하는 노드 검색 패널.', 'Панель поиска узлов с поддержкой разных языков и приоритетом избранного.', 'Buscador de nodos multilingüe con prioridad para los favoritos.'),
    'Snippet category: {category}': ('组合点类目：{category}', 'スニペットのカテゴリ: {category}', '스니펫 범주: {category}', 'Категория сниппета: {category}', 'Categoría del fragmento: {category}'),
    'Reset Size': ('恢复默认大小', 'サイズをリセット', '크기 초기화', 'Сбросить масштаб', 'Restablecer escala'),
    'Move Shortcut': ('移动快捷节点', 'クイックノードを移動', '빠른 노드 이동', 'Переместить быстрый узел', 'Mover acceso rápido'),
    'Shortcut Key': ('搜索快捷键按键', '検索キー', '검색 단축키', 'Клавиша поиска', 'Tecla de búsqueda'),
    'Snippet Shortcut Key': ('组合点快捷键按键', 'スニペット保存キー', '스니펫 저장 키', 'Клавиша сохранения сниппета', 'Tecla para guardar fragmento'),
    'Space': ('空格', 'スペース', '스페이스', 'Пробел', 'Espacio'),
    'Show only English names': ('仅显示英文名称', '英語名のみを表示', '영어 이름만 표시', 'Показывать только английские имена', 'Mostrar solo nombres en inglés'),
    'Show selected language names where available': ('有译名时显示所选语言名称', '翻訳がある場合は選択した言語で表示', '번역이 있으면 선택한 언어로 표시', 'Показывать имена на выбранном языке при наличии перевода', 'Mostrar nombres en el idioma seleccionado cuando estén traducidos'),
    'English names first': ('英文名称在前', '英語名を先に表示', '영어 이름을 먼저 표시', 'Английские имена первыми', 'Nombres en inglés primero'),
    'Selected language names first': ('所选语言名称在前', '選択した言語を先に表示', '선택한 언어를 먼저 표시', 'Имена на выбранном языке первыми', 'Idioma seleccionado primero'),
    'Use English only, or search English and a second language using Blender\'s installed translations': ('使用纯英文，或通过 Blender 已安装的译名搜索英文及第二语言', '英語のみ、または Blender の翻訳を使って英語と選択言語で検索します', '영어만 사용하거나 Blender의 번역으로 영어와 선택 언어를 검색합니다', 'Поиск только на английском или на английском и выбранном языке с переводами Blender', 'Busca solo en inglés o en inglés y otro idioma con las traducciones instaladas de Blender'),
    'Include published prereleases when checking for updates; does not install automatically': ('检查更新时包含已发布的测试版本，不会自动安装', '更新確認に公開済みのプレリリースを含めます。自動インストールはしません', '업데이트 확인 시 공개된 사전 릴리스를 포함합니다. 자동 설치하지 않습니다', 'Включать предварительные выпуски при проверке; без автоматической установки', 'Incluye versiones preliminares publicadas al comprobar; no instala automáticamente'),
    'How node names are shown in the custom search panel': ('节点名称在搜索面板中的显示方式', '検索画面でのノード名の表示方法', '검색 패널에 노드 이름을 표시하는 방식', 'Способ отображения имён узлов в поиске', 'Cómo se muestran los nombres de nodos en el buscador'),
    "Allow sparse Chinese/pinyin matching such as '设置法向' matching '设置曲线法向'. May make searching slightly slower.": ('允许跳字匹配中文或拼音，例如“设置法向”匹配“设置曲线法向”，可能略微降低搜索速度', '中国語・ピンインの部分的な一致を許可します。検索が少し遅くなる場合があります', '중국어와 병음의 불연속 일치를 허용합니다. 검색이 약간 느려질 수 있습니다', 'Разрешить разреженное сопоставление китайского текста и пиньиня; поиск может стать медленнее', 'Permite coincidencias no contiguas en chino y pinyin; puede ralentizar la búsqueda'),
    'Keyboard key used to open Node Console in the node editor': ('在节点编辑器中打开 Node Console 的按键', 'ノードエディターで Node Console を開くキー', '노드 편집기에서 Node Console을 여는 키', 'Клавиша открытия Node Console в редакторе узлов', 'Tecla para abrir Node Console en el editor de nodos'),
    'Require Shift for the Node Console shortcut': ('打开搜索时需要同时按住 Shift', '検索を開くときに Shift が必要', '검색을 열 때 Shift 필요', 'Требовать Shift для открытия поиска', 'Requerir Shift para abrir el buscador'),
    'Require Ctrl for the Node Console shortcut': ('打开搜索时需要同时按住 Ctrl', '検索を開くときに Ctrl が必要', '검색을 열 때 Ctrl 필요', 'Требовать Ctrl для открытия поиска', 'Requerir Ctrl para abrir el buscador'),
    'Require Alt for the Node Console shortcut': ('打开搜索时需要同时按住 Alt', '検索を開くときに Alt が必要', '검색을 열 때 Alt 필요', 'Требовать Alt для открытия поиска', 'Requerir Alt para abrir el buscador'),
    'Require Command for the Node Console shortcut on macOS': ('macOS 上打开搜索时需要同时按住 Command', 'macOS で検索を開くときに Command が必要', 'macOS에서 검색을 열 때 Command 필요', 'Требовать Command для открытия поиска в macOS', 'Requerir Command para abrir el buscador en macOS'),
    'Keyboard key used to save selected nodes as a snippet node': ('将选中节点保存为组合点的按键', '選択ノードをスニペットとして保存するキー', '선택한 노드를 스니펫으로 저장하는 키', 'Клавиша сохранения выбранных узлов в сниппет', 'Tecla para guardar los nodos seleccionados como fragmento'),
    'Require Shift for the snippet node shortcut': ('保存组合点时需要同时按住 Shift', 'スニペットの保存に Shift が必要', '스니펫 저장 시 Shift 필요', 'Требовать Shift для сохранения сниппета', 'Requerir Shift para guardar el fragmento'),
    'Require Ctrl for the snippet node shortcut': ('保存组合点时需要同时按住 Ctrl', 'スニペットの保存に Ctrl が必要', '스니펫 저장 시 Ctrl 필요', 'Требовать Ctrl для сохранения сниппета', 'Requerir Ctrl para guardar el fragmento'),
    'Require Alt for the snippet node shortcut': ('保存组合点时需要同时按住 Alt', 'スニペットの保存に Alt が必要', '스니펫 저장 시 Alt 필요', 'Требовать Alt для сохранения сниппета', 'Requerir Alt para guardar el fragmento'),
    'Require Command for the snippet node shortcut on macOS': ('macOS 上保存组合点时需要同时按住 Command', 'macOS でスニペットの保存に Command が必要', 'macOS에서 스니펫 저장 시 Command 필요', 'Требовать Command для сохранения сниппета в macOS', 'Requerir Command para guardar el fragmento en macOS'),
    'External JSON file used to store snippet nodes': ('用于保存组合点的外部 JSON 文件', 'スニペットを保存する外部 JSON ファイル', '스니펫을 저장하는 외부 JSON 파일', 'Внешний JSON-файл для хранения сниппетов', 'Archivo JSON externo que almacena los fragmentos'),
    'Show saved snippet nodes in preferences': ('在偏好设置中展开已保存的组合点', '保存済みスニペットを設定画面に表示', '환경설정에서 저장된 스니펫 표시', 'Показывать сохранённые сниппеты в настройках', 'Mostrar los fragmentos guardados en preferencias'),
    'Show cached Asset Library node groups in search results. Refresh Asset Index updates the cache.': ('在搜索结果中显示用户资产库已缓存的节点组。“刷新资产索引”会更新缓存', 'ユーザーアセットライブラリのキャッシュ済みノードグループを検索に表示します。索引更新でキャッシュを更新します', '검색 결과에 사용자 에셋 라이브러리의 캐시된 노드 그룹을 표시합니다. 에셋 색인 갱신으로 캐시를 업데이트합니다', 'Показывать в поиске кэшированные группы из пользовательских библиотек. Обновление индекса обновляет кэш', 'Muestra grupos de nodos en caché de bibliotecas propias. Actualizar el índice renueva la caché'),
    'How category colors are shown in Node Console search results': ('类目颜色在搜索结果中的显示方式', '検索結果でのカテゴリ色の表示方法', '검색 결과의 범주 색상 표시 방식', 'Способ отображения цветов категорий в поиске', 'Cómo se muestran los colores de categoría en los resultados'),
    'Show a slim category color line at the left edge': ('在左侧显示一条类目颜色竖线', '左端にカテゴリ色の細い線を表示', '왼쪽 가장자리에 범주 색상의 가는 선 표시', 'Тонкая цветная линия категории слева', 'Mostrar una línea fina de color de categoría a la izquierda'),
    'Show colored category backgrounds': ('显示类目颜色底块', 'カテゴリの背景に色を表示', '범주 배경에 색상 표시', 'Цветной фон категорий', 'Mostrar fondos de color para las categorías'),
    'Hide category color decorations': ('关闭类目颜色装饰', 'カテゴリ色の装飾を非表示', '범주 색상 장식 숨기기', 'Скрыть цветовое оформление категорий', 'Ocultar la decoración de color de categorías'),
    'Adjust the Node Console text and panel size': ('调整 Node Console 的文字和面板大小', 'Node Console の文字とパネルのサイズを調整', 'Node Console의 글자와 패널 크기 조절', 'Изменить размер текста и панели Node Console', 'Ajustar el tamaño del texto y del panel de Node Console'),
    'Adjust the Node Console panel width': ('调整 Node Console 的面板宽度', 'Node Console のパネル幅を調整', 'Node Console 패널 너비 조절', 'Изменить ширину панели Node Console', 'Ajustar el ancho del panel de Node Console'),
    'Scan Blender asset node groups and cache them for fast search': ('扫描 Blender 资产节点组并建立缓存，以便快速搜索', 'Blender のアセットノードグループを走査し検索用にキャッシュ', 'Blender 에셋 노드 그룹을 스캔하여 빠른 검색용 캐시 생성', 'Сканировать группы узлов-ассетов Blender и создать кэш для быстрого поиска', 'Explorar grupos de nodos de recursos de Blender y guardarlos en caché para buscar rápido'),
    'Reset Node Console width to the default value': ('将搜索窗口宽度恢复为默认值', '検索画面の幅を既定値に戻す', '검색 창 너비를 기본값으로 복원', 'Восстановить ширину поиска по умолчанию', 'Restablecer el ancho predeterminado del buscador'),
    'Reset Node Console size to the platform default value': ('将搜索窗口大小恢复为当前平台的默认值', '検索画面のサイズをプラットフォームの既定値に戻す', '검색 창 크기를 현재 플랫폼의 기본값으로 복원', 'Восстановить масштаб поиска по умолчанию для платформы', 'Restablecer la escala predeterminada del buscador para esta plataforma'),
    'Save selected nodes as a reusable Node Console snippet': ('将选中节点保存为可重复使用的组合点', '選択ノードを再利用できるスニペットとして保存', '선택한 노드를 재사용 가능한 스니펫으로 저장', 'Сохранить выбранные узлы как повторно используемый сниппет', 'Guardar los nodos seleccionados como fragmento reutilizable'),
    'Name used to search this snippet': ('用于搜索此组合点的名称', 'スニペットの検索に使う名前', '스니펫 검색에 사용할 이름', 'Имя для поиска этого сниппета', 'Nombre para buscar este fragmento'),
    'Category color and grouping for this snippet': ('此组合点的归类及类目颜色', 'スニペットのカテゴリと色', '스니펫의 범주와 색상', 'Категория и цвет этого сниппета', 'Categoría y color de este fragmento'),
    'Remove this saved Node Console snippet': ('删除此已保存的组合点', 'この保存済みスニペットを削除', '저장된 이 스니펫 삭제', 'Удалить этот сохранённый сниппет', 'Eliminar este fragmento guardado'),
    'Remove this node from Node Console favorites': ('从收藏中移除此节点', 'このノードをお気に入りから削除', '즐겨찾기에서 이 노드 제거', 'Удалить этот узел из избранного', 'Quitar este nodo de favoritos'),
    'Remove this node shortcut': ('从快捷列表中移除此节点', 'このノードをクイックノードから削除', '빠른 노드 목록에서 이 노드 제거', 'Удалить этот узел из списка быстрых узлов', 'Quitar este nodo de la lista de acceso rápido'),
    'Move this shortcut': ('调整此快捷节点的顺序', 'このクイックノードの順番を変更', '이 빠른 노드의 순서 변경', 'Изменить порядок этого быстрого узла', 'Cambiar el orden de este acceso rápido'),
    'Read available GitHub releases without installing anything': ('检查 GitHub 上可用的版本，不会直接安装', 'GitHub の公開バージョンを確認します。インストールはしません', 'GitHub의 사용 가능한 버전을 확인합니다. 설치하지 않습니다', 'Проверить доступные выпуски GitHub без установки', 'Consultar las versiones de GitHub sin instalar nada'),
    'Confirm the selected release before downloading and replacing the add-on': ('确认所选版本后再下载并替换插件', '選択バージョンを確認してからダウンロード・置換', '선택한 버전을 확인한 후 다운로드하여 애드온 교체', 'Подтвердить версию перед загрузкой и заменой дополнения', 'Confirmar la versión antes de descargar y reemplazar el complemento'),
    'Search and add nodes': ('搜索并添加节点', 'ノードを検索して追加', '노드 검색 및 추가', 'Поиск и добавление узлов', 'Buscar y añadir nodos'),
    'Node Console cached {count} asset node groups': ('Node Console 已缓存 {count} 个资产节点组', 'Node Console: {count} 個のアセットノードグループをキャッシュしました', 'Node Console: 에셋 노드 그룹 {count}개 캐시 완료', 'Node Console: групп узлов-ассетов в кэше: {count}', 'Node Console: {count} grupos de nodos guardados en caché'),
}
EXTRA_ZH = {key: row[0] for key, row in DETAILS.items()}
ROWS.update({key: row[1:] for key, row in DETAILS.items()})


def language_code(language, system_locale='en_US', enabled=True):
    if not enabled:
        return 'en'
    language = system_locale if language == 'DEFAULT' else language
    code = str(language).replace('-', '_').split('_')[0]
    return code if code in ('en', 'zh', *LANGUAGES) else 'en'


def catalogs(chinese):
    result = {'zh': dict(chinese, **EXTRA_ZH), 'en': {}}
    result.update({code: {key: row[index] for key, row in ROWS.items()}
                   for index, code in enumerate(LANGUAGES)})
    for code, messages in result.items():
        if code == 'en':
            continue
        for category in ('Input', 'Output', 'Geometry', 'Shader', 'Color', 'Converter',
                         'Vector', 'Texture', 'Filter', 'Mask', 'Distort', 'Utility', 'Layout', 'Uncategorized'):
            source = category + ('-style snippets' if category in ('Input', 'Output') else ' snippets')
            messages[source] = messages['Snippet category: {category}'].format(category=messages[category])
    return result


def blender_catalog(catalog):
    result = {locale: {(CONTEXT, key): value for key, value in catalog[code].items()}
              for locale, code in LOCALES.items()}
    # Blender draws add-on metadata without a custom context. Only expose our
    # unique full description here, never shared labels such as "Color".
    for locale, code in LOCALES.items():
        result[locale][('*', ADDON_DESCRIPTION)] = catalog[code][ADDON_DESCRIPTION]
    return result
