"""Точка входа: загрузка конфигурации и построение графа зависимостей."""

import argparse
import sys

from src.config import ConfigError, load_config
from src.d2 import format_d2
from src.file_repo import FileRepoError, FileRepository
from src.graph import build_graph, format_graph
from src.maven import make_coordinates
from src.maven_source import MavenSource
from src.order import compute_load_order, format_order
from src.pom import MavenError
from src.render import RenderError, save_diagram
from src.tree import format_tree

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
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="сохранить граф на языке D2 и отрисовать PNG",
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


def render_text(graph, root, config, load_order):
    """Подготовить строки вывода для выбранного режима."""
    if load_order:
        order, cycles = compute_load_order(graph, root)
        return format_order(order, cycles)
    if config.ascii_tree:
        return format_tree(graph, root)
    return format_graph(graph)


def visualize(graph, root, config):
    """Сохранить D2 и PNG, вернуть сообщения о созданных файлах."""
    d2_path = save_diagram(format_d2(graph, root), config.output_file)
    return [f"Диаграмма D2: {d2_path}", f"Изображение: {config.output_file}"]


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        source, root = create_source(config)
        graph = build_graph(root, source, config.filter_substring)
        messages = visualize(graph, root, config) if args.visualize else []
    except (ConfigError, MavenError, FileRepoError, RenderError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    lines = render_text(graph, root, config, args.load_order)
    print("\n".join(messages + lines))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
