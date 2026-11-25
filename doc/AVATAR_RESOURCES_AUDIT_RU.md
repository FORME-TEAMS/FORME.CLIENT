# Проверка ресурсов клиента — 25 ноября 2026

Основа: `FORME-TEAMS/FORME.CLIENT`, ветка `fix/macos-universal-vlc-plugins`,
commit `a882c4e55303c545775d7edd233507e3ef01bfb9`.

При сравнении с сохранённой историей клиента обнаружены 91 удалённый файл
встроенной геометрии и текстур в `indra/newview/character`. В `avatar_lad.xml`
85 ссылок указывали на отсутствовавшие `.llm`/`.tga`; мешей и TGA в каталоге
вообще не было. Manifest разрешал отсутствие обоих наборов через `path_optional`.

Ресурсы восстановлены из сохранённого commit `93a9ae5b` предыдущей истории
клиента (техническая основа `9f7062fa`). Менять вид, UUID или протокол аватара для
этого не нужно. Возвращены также `res/viewerRes.rc` и две платформенные PNG-иконки,
удалённые при переносе: первый используется Windows CMake, иконки — упаковкой.
Существующие copyright/license notices сохранены.

Manifest снова требует meshes/textures. Preflight дополнительно обходит фактические
ссылки `avatar_lad.xml`, чтобы частично потерянный набор тоже приводил к ошибке.
`.gitignore` больше не исключает встроенные character assets и необходимые
ресурсные шаблоны/иконки платформ.

Локальная проверка:

- полный `python3 scripts/forme_preflight.py` прошёл, включая проверки macOS
  manifest/universal bundle и отсутствие VOICE;
- удаление одного `avatar_head.llm` контролируемо приводит к ошибке preflight;
  файл после теста восстановлен;
- `g++ -fsyntax-only` с имеющимся Linux SDK прошёл для изменённых при переносе
  `fsformeinventory.cpp`, `exogroupmutelist.cpp`, `llviewerfloaterreg.cpp` и
  `llviewerassetstorage.cpp`. Это проверка C++, а не линковка приложения macOS.

Первопричина серверного HTTP 400 находится в серверном `LLLoginService`, а не в
клиенте. Для восстановления входа нужно обновить сервер. Серверный разбор:
`FORME-TEAMS/FORME.SERVER`, `doc/real-world/LOGIN-REGION-AUDIT-20261125.md`.

CI и установочная сборка не запускались; macOS/Windows binary и графическая
игровая приёмка не заявляются. RWS-005 остаётся `in_progress`.
