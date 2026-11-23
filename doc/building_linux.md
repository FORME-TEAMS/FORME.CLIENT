# ForMe.World: сборка Linux x86_64

Исходная среда для воспроизведения — Ubuntu 22.04 x86_64. Другие дистрибутивы и версии требуют собственной проверки зависимостей и полной линковки. Нужны 16 ГБ RAM и не менее 64 ГБ свободного места.

## Подготовка

[Получите исходники](BUILD.md). Установите зависимости:

```sh
sudo apt update
sudo apt install build-essential gcc-11 g++-11 python3-pip python3-venv git pkg-config patch   libgl1-mesa-dev libglu1-mesa-dev libpulse-dev libssl-dev libxinerama-dev   libxrandr-dev libfontconfig1-dev libfreetype6-dev libxrender-dev libxext-dev libxi-dev
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt 'cmake>=3.28,<4'
export CC=gcc-11
export CXX=g++-11
```

При повторном открытии терминала снова активируйте окружение и задайте CC/CXX.

## Компиляция и запуск

```sh
python scripts/forme_client.py configure
python scripts/forme_client.py build --jobs 3
python scripts/forme_client.py run
```

После любой ошибки остановитесь и сохраните первую ошибку журнала. Для своей сети используйте `configure --grid-url` по [общему руководству](BUILD.md).

Результат находится в `build-linux-x86_64`. Сохраняйте рядом ресурсы и библиотеки. Этот путь не создаёт AppImage или установочный пакет; полноценная Linux-упаковка и проверка на чистой системе остаются отдельной работой. Инструкция не является подтверждением успешной Linux-сборки нового репозитория.
