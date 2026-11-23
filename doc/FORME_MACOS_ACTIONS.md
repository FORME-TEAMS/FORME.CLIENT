# ForMe.World: ручная сборка macOS в GitHub Actions

В закрытом репозитории откройте **Actions → ForMe.World — macOS → Run workflow**. Выберите `main` или проверяемую рабочую ветку, проверьте адрес служб входа и подтвердите запуск. Права на чтение исходников и запуск Actions выдаются владельцем репозитория.

Эта сборка не запускается коммитами или по расписанию. Она использует Xcode 16.4, публичные зависимости и закреплённый набор переменных. Собирается универсальное приложение Intel/Apple Silicon с локальной подписью; Apple Developer сертификат и нотариальное заверение не используются.

## Запуск через терминал

```sh
gh auth login
gh workflow run forme-macos.yml --repo FORME-TEAMS/FORME.CLIENT --ref main
gh run list --repo FORME-TEAMS/FORME.CLIENT --workflow forme-macos.yml --limit 5
```

Из списка возьмите ID именно нового запуска:

```sh
FORME_RUN_ID=1234567890
gh run watch "$FORME_RUN_ID" --repo FORME-TEAMS/FORME.CLIENT --exit-status
gh run download "$FORME_RUN_ID" --repo FORME-TEAMS/FORME.CLIENT   --name ForMe.World-macOS --dir ./download
```

ID в примере замените настоящим. Скачивание приложения выполняйте после успешного завершения сборки. Артефакт **ForMe.World-macOS** содержит `ForMe.World-macOS-universal.zip`. Доступ к артефактам закрыт доступом к репозиторию; срок хранения — 14 дней.

При ошибке:

```sh
gh run view "$FORME_RUN_ID" --repo FORME-TEAMS/FORME.CLIENT --log-failed
gh run download "$FORME_RUN_ID" --repo FORME-TEAMS/FORME.CLIENT   --name ForMe.World-macOS-logs --dir ./build-logs
```

Готовый архив загружается только после успешных компиляции, проверки ресурсов и подписи. Артефакт логов не является приложением. Actions может требовать доступных минут/квоты аккаунта; создание репозитория само по себе не означает выполненную сборку.
