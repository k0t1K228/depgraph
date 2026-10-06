"""Точка входа: загрузка конфигурации и вывод прямых зависимостей."""

import argparse
import sys

from src.config import ConfigError, load_config
from src.maven import get_direct_dependencies, make_coordinates
from src.pom import MavenError

EXIT_OK = 0
EXIT_ERROR = 1
UNKNOWN_VERSION = "?"
TEST_MODE_MESSAGE = "тестовый режим будет реализован на этапе 3"

def parse_args(argv):
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей Maven-пакетов."
    )
    parser.add_argument("config", help="путь к CSV-файлу конфигурации")
    return parser.parse_args(argv)

def format_dependency(dependency):
    """Преобразовать зависимость в строку «группа:артефакт:версия»."""
    version = dependency.version or UNKNOWN_VERSION
    line = f"{dependency.group}:{dependency.artifact}:{version}"
    line += f" [{dependency.scope}]"
    if dependency.optional:
        line += " (optional)"
    return line

def print_dependencies(config, dependencies):
    """Вывести прямые зависимости пакета."""
    print(f"Прямые зависимости {config.package_name}:{config.version}:")
    if not dependencies:
        print("  (нет)")
    for dependency in dependencies:
        print(f"  {format_dependency(dependency)}")

def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        if config.test_mode:
            raise MavenError(TEST_MODE_MESSAGE)
        coords = make_coordinates(config.package_name, config.version)
        dependencies = get_direct_dependencies(config.repository, coords)
    except (ConfigError, MavenError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_dependencies(config, dependencies)
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
