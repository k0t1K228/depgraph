"""Точка входа: загрузка конфигурации и построение графа зависимостей."""

import argparse
import sys

from src.config import ConfigError, load_config
from src.file_repo import FileRepoError, FileRepository
from src.graph import build_graph, format_graph
from src.maven import make_coordinates
from src.maven_source import MavenSource
from src.order import compute_load_order, format_order
from src.pom import MavenError

EXIT_OK = 0
EXIT_ERROR = 1


def parse_args(argv):
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей Maven-пакетов."
    )
    parser.add_argument("config", help="путь к CSV-файлу конфигурации")
    parser.add_argument(
        "--load-order",
        action="store_true",
        help="вывести порядок загрузки зависимостей вместо графа",
    )
    return parser.parse_args(argv)


def create_source(config):
    """Создать источник зависимостей и вернуть его вместе с корнем."""
    if config.test_mode:
        repository = FileRepository.from_file(config.repository)
        repository.require(config.package_name)
        return repository, config.package_name
    coords = make_coordinates(config.package_name, config.version)
    source = MavenSource(config.repository, coords)
    return source, source.root


def render(graph, root, load_order):
    """Подготовить строки вывода для выбранного режима."""
    if load_order:
        order, cycles = compute_load_order(graph, root)
        return format_order(order, cycles)
    return format_graph(graph)


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        source, root = create_source(config)
        graph = build_graph(root, source, config.filter_substring)
    except (ConfigError, MavenError, FileRepoError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print("\n".join(render(graph, root, args.load_order)))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
