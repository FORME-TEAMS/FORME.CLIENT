# ForMe.World: сборка Windows x64

## Инструменты

- Windows 10/11 x64, 16 ГБ RAM, 64 ГБ свободного места.
- Visual Studio 2022 с **Desktop development with C++**, MSVC v143 и Windows SDK.
- Git, GitHub CLI и Python 3.11 x64 с pip.
- Cygwin x64: пакеты `patch`, `gcc-g++`, `make`. Его каталог `bin` должен быть в PATH; `c++ --version` должен выполняться. Эти инструменты нужны также предварительным C++ проверкам.

Откройте **x64 Native Tools Command Prompt for VS 2022**. Все команды ниже предназначены для этого cmd-окна. [Получите исходники](BUILD.md), затем:

```bat
py -3.11 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt "cmake>=3.28,<4"
cl
c++ --version
cmake --version
autobuild --version
```

У `cl` без входного файла ожидается сообщение компилятора с ошибкой отсутствия исходника; это проверка наличия инструмента. Путь проекта должен быть коротким, например `C:\ForMe\Client`.

## Компиляция

```bat
python scripts\forme_client.py configure
if errorlevel 1 exit /b 1
python scripts\forme_client.py build --jobs 3
if errorlevel 1 exit /b 1
python scripts\forme_client.py run
```

Индивидуальный URL задаётся параметром `configure --grid-url`, как в [общем руководстве](BUILD.md). Компиляция создаёт рабочий каталог `build-vc170-64`; не переносите из него один exe без DLL и ресурсов.

Команда `bundle` сейчас относится только к macOS. Автоматический установщик Windows и его подпись этим руководством не объявляются готовыми. Нужны отдельные полная Windows-сборка, упаковка и запуск на чистой системе. При неуспешном build команда run не выполняется.
