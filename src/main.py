"""Точка входа: загрузка конфигурации и вывод параметров."""

import argparse
import sys
from dataclasses import asdict

from src.config import ConfigError, load_config

EXIT_OK = 0
EXIT_ERROR = 1

def parse_args(argv):
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей Maven-пакетов."
    )
    parser.add_argument("config", help="путь к CSV-файлу конфигурации")
    return parser.parse_args(argv)

def format_value(value):
    """Преобразовать значение параметра в строку для вывода."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)

def print_config(config):
    """Вывести все параметры в формате «ключ: значение»."""
    for key, value in asdict(config).items():
        print(f"{key}: {format_value(value)}")

def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_config(config)
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
