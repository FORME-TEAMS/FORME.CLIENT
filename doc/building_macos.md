# ForMe.World: сборка macOS

Результат — универсальное приложение для Intel и Apple Silicon. Сначала [получите исходники](BUILD.md) и откройте Terminal в корне проекта.

## Подготовка

1. Установите полный Xcode 16.4 из Apple Developer Downloads, запустите его и завершите установку компонентов. Одних Command Line Tools недостаточно.
2. Выберите установленный Xcode и примите его лицензию:

```sh
sudo xcode-select --switch /Applications/Xcode_16.4.app/Contents/Developer
sudo xcodebuild -license accept
xcodebuild -version
```

Если Xcode установлен как `/Applications/Xcode.app`, укажите этот путь. Сборка использует выбранный Xcode; его версия должна совпадать с требуемой.

3. Установите Homebrew, затем инструменты:

```sh
brew install python@3.11 bash gnu-sed pkg-config git
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt 'cmake>=3.28,<4'
export PATH="$(brew --prefix bash)/bin:$(brew --prefix gnu-sed)/libexec/gnubin:$PATH"
python --version
cmake --version
autobuild --version
```

Не используйте `sudo pip`. При повторном открытии Terminal активируйте `.venv` и снова задайте PATH.

## Компиляция и упаковка

Каждая следующая команда выполняется только после успешной предыдущей:

```sh
python scripts/forme_client.py configure
python scripts/forme_client.py build --jobs 3
python scripts/forme_client.py bundle
python scripts/forme_client.py run
```

Для другого адреса служб входа передайте `--grid-url` команде configure; пример находится в [общем руководстве](BUILD.md).

Готовые файлы:

- `dist/ForMe.World.app` — приложение для локального запуска;
- `dist/ForMe.World-macOS-universal.zip` — архив для передачи.

ZIP сохраняет права и символические ссылки приложения. Распаковывайте его средствами macOS. Для установки перенесите приложение в Applications.

Подпись локальная, без сертификата Apple Developer и нотариального заверения. Это не нотариально заверенный установщик. macOS может запросить подтверждение запуска доверенного локального приложения через System Settings → Privacy & Security. Не отключайте системную защиту целиком.

Полный configure/build выполняется на macOS; предварительные проверки на другой ОС не подтверждают линковку или запуск приложения.
