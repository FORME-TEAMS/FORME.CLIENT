#!/usr/bin/env python3
# Copyright (c) 2026 ForMe.World contributors. SPDX-License-Identifier: LGPL-2.1-only
"""ForMe.World build entry point. Downloads public dependencies, never publishes builds."""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
VARIABLES_COMMIT = 'c17312d38377c003977cf5b6dcc83c6042eba194'
VARIABLES_REPO = 'https://github.com/FirestormViewer/fs-build-variables.git'
CONFIGURATION = 'ReleaseFS_open'


def run(args, env=None):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, env=env, check=True)


def build_directory():
    if sys.platform == 'darwin':
        return ROOT / 'build-darwin-universal'
    if sys.platform == 'win32':
        return ROOT / 'build-vc170-64'
    if sys.platform.startswith('linux') and platform.machine().lower() in ('x86_64', 'amd64'):
        return ROOT / 'build-linux-x86_64'
    raise ValueError('Для этой платформы профиль сборки пока не подготовлен.')


def environment():
    env = os.environ.copy()
    env.update(AUTOBUILD_ADDRSIZE='64', AUTOBUILD_VSVER='170',
               AUTOBUILD_VARIABLES_FILE=str(ROOT / 'build-variables/variables'))
    env.setdefault('AUTOBUILD_BUILD_ID', '0')
    env.setdefault('PYTHON', sys.executable)
    return env


def variables():
    target = ROOT / 'build-variables'
    if not target.exists():
        target.mkdir()
        run(['git', 'init', target])
    if not (target / '.git').is_dir():
        raise ValueError('build-variables занят другим каталогом. Сохраните его под другим именем.')
    origin = subprocess.run(['git', '-C', str(target), 'remote', 'get-url', 'origin'],
                            capture_output=True, text=True)
    if origin.returncode:
        run(['git', '-C', target, 'remote', 'add', 'origin', VARIABLES_REPO])
    elif origin.stdout.strip() != VARIABLES_REPO:
        raise ValueError('У build-variables другой источник. Используйте отдельный чистый каталог сборки.')
    dirty = subprocess.check_output(['git', '-C', str(target), 'status', '--porcelain'], text=True)
    if dirty:
        raise ValueError('В build-variables есть локальные изменения; сохраните их перед сборкой.')
    current = subprocess.run(['git', '-C', str(target), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    if current.stdout.strip() != VARIABLES_COMMIT:
        run(['git', '-C', target, 'fetch', '--depth=1', 'origin', VARIABLES_COMMIT])
        run(['git', '-C', target, 'checkout', '--detach', 'FETCH_HEAD'])
    if not (target / 'variables').is_file():
        raise ValueError('В наборе переменных отсутствует файл variables.')


def login_url(value):
    uri = urlsplit(value)
    if uri.scheme not in ('http', 'https') or not uri.hostname or uri.username or uri.password or uri.query or uri.fragment:
        raise argparse.ArgumentTypeError('Укажите HTTP(S) URL служб входа без пароля, query или fragment.')
    return value.rstrip('/') + '/'


def check():
    run([sys.executable, ROOT / 'scripts/forme_preflight.py'])


def configure(url):
    check()
    variables()
    run(['autobuild', 'configure', '-c', CONFIGURATION, '-A64', '--',
         '--chan', 'ForMe.World', '--opensim', '--singlegrid', url, '--no-package',
         '-DINSTALL_PROPRIETARY:BOOL=OFF', '-DUSE_OPENAL:BOOL=ON',
         '-DUSE_BUGSPLAT:BOOL=OFF', '-DBUGSPLAT_DB:STRING=', '-DUSE_DISCORD:BOOL=OFF'], environment())


def build(jobs):
    directory = build_directory()
    if not (directory / 'CMakeCache.txt').is_file():
        raise ValueError('Сначала выполните configure из корня репозитория.')
    run(['cmake', '--build', directory, '--config', 'Release', '--parallel', str(jobs)], environment())



def verify_universal_app(app):
    """Require a universal app and plugin host; allow thin optional VLC modules.

    VLC ships architecture-specific codec plugins (for example the x86 MMX
    plugin). Those modules are optional runtime extensions, not part of the
    viewer's executable ABI. The loader can use modules matching the running
    process architecture, so requiring every plugin to be a fat binary would
    incorrectly reject an otherwise universal application.
    """
    required = {'arm64', 'x86_64'}
    vlc_plugins = Path('Contents/Resources/SLPlugin.app/Contents/Frameworks/plugins')
    checked = 0
    thin_plugins = []
    for root, _, files in os.walk(app):
        for name in files:
            path = Path(root) / name
            description = subprocess.run(
                ['file', '-b', path], capture_output=True, text=True,
                encoding='utf-8', errors='replace', check=True
            ).stdout
            if 'Mach-O' not in description:
                continue
            result = subprocess.run(
                ['lipo', '-archs', path], capture_output=True, text=True,
                encoding='utf-8', errors='replace'
            )
            if result.returncode:
                raise ValueError(f'Не удалось проверить архитектуры {path}: {result.stderr.strip()}')
            architectures = set(result.stdout.split())
            missing = required - architectures
            relative = path.relative_to(app)
            is_optional_vlc_plugin = vlc_plugins in relative.parents
            if is_optional_vlc_plugin and missing:
                if not (architectures & required):
                    raise ValueError(
                        f'VLC-плагин {path} не поддерживает arm64 или x86_64; '
                        f'обнаружены: {", ".join(sorted(architectures))}'
                    )
                thin_plugins.append((path, architectures))
                continue
            if missing:
                raise ValueError(
                    f'В обязательном бинарнике {path} отсутствуют архитектуры: '
                    f'{", ".join(sorted(missing))}; обнаружены: {", ".join(sorted(architectures))}'
                )
            checked += 1
    if checked == 0:
        raise ValueError('В приложении не найдено ни одного обязательного Mach-O бинарника.')
    print(f'ForMe.World: Universal Binary подтверждён для {checked} обязательных Mach-O файлов '
          '(arm64 + x86_64).')
    if thin_plugins:
        print(f'ForMe.World: оставлено {len(thin_plugins)} архитектурно-зависимых VLC-плагинов:')
        for path, architectures in thin_plugins:
            print(f'  {path}: {", ".join(sorted(architectures))}')


def bundle():
    if sys.platform != 'darwin':
        raise ValueError('Команда bundle пока предназначена для macOS; на других системах доступна build.')
    app = build_directory() / 'newview/Release/Firestorm.app'
    binary = app / 'Contents/MacOS/Firestorm'
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError('Собранное приложение не найдено. Сначала успешно завершите build.')
    if not (app / 'Contents/Resources/app_settings/settings.xml').is_file():
        raise ValueError('В приложении отсутствуют обязательные ресурсы.')
    stage = ROOT / 'dist/ForMe.World.app'
    archive = ROOT / 'dist/ForMe.World-macOS-universal.zip'
    stage.parent.mkdir(exist_ok=True)
    if stage.exists():
        shutil.rmtree(stage)
    run(['ditto', app, stage])
    verify_universal_app(stage)
    run(['codesign', '--force', '--deep', '--sign', '-', stage])
    run(['codesign', '--verify', '--deep', '--strict', stage])
    archive.unlink(missing_ok=True)
    run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', stage, archive])
    run(['unzip', '-t', archive])
    print('ForMe.World: архив готов:', archive)


def launch():
    directory = build_directory() / 'newview'
    if sys.platform == 'darwin':
        app = ROOT / 'dist/ForMe.World.app'
        if not app.is_dir():
            raise ValueError('Сначала выполните bundle.')
        run(['open', app])
    else:
        binary = directory / ('Release/firestorm-bin.exe' if sys.platform == 'win32' else 'firestorm-bin')
        if not binary.is_file():
            raise ValueError('Исполняемый файл не найден; проверьте журнал build.')
        subprocess.Popen([str(binary)], cwd=binary.parent)


def main():
    parser = argparse.ArgumentParser(description='Компиляция клиента ForMe.World')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('check', help='Проверить исходники и интерфейс перед компиляцией')
    config = commands.add_parser('configure', help='Подготовить профиль сборки и публичные зависимости')
    config.add_argument('--grid-url', type=login_url,
                        default=os.environ.get('FORME_WORLD_LOGIN_URI', 'http://185.173.93.200:8002/'))
    compile_command = commands.add_parser('build', help='Скомпилировать подготовленный профиль')
    compile_command.add_argument('--jobs', type=int, choices=range(1, 65), default=3, metavar='1..64')
    commands.add_parser('bundle', help='Подготовить архив приложения для macOS')
    commands.add_parser('run', help='Запустить успешно собранное приложение')
    args = parser.parse_args()
    try:
        if args.command == 'check': check()
        elif args.command == 'configure': configure(args.grid_url)
        elif args.command == 'build': build(args.jobs)
        elif args.command == 'bundle': bundle()
        elif args.command == 'run': launch()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('ForMe.World: ' + str(error), file=sys.stderr)
        return error.returncode if isinstance(error, subprocess.CalledProcessError) else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
