"""Источник зависимостей для обхода графа: репозиторий Maven."""

import sys

from src.maven import get_direct_dependencies
from src.pom import Coordinates, MavenError

TRANSITIVE_SCOPES = ("compile", "runtime")
NODE_SEPARATOR = ":"
UNKNOWN_VERSION = "?"


def make_node(group, artifact, version):
    """Собрать идентификатор вершины «группа:артефакт:версия»."""
    return NODE_SEPARATOR.join((group, artifact, version))


def parse_node(node):
    """Разобрать идентификатор вершины в координаты."""
    group, artifact, version = node.split(NODE_SEPARATOR)
    return Coordinates(group, artifact, version)


def is_transitive(dependency):
    """Проверить, попадает ли зависимость в транзитивные."""
    return dependency.scope in TRANSITIVE_SCOPES and not dependency.optional


class MavenSource:
    """Источник зависимостей: реальный репозиторий Maven по URL."""

    def __init__(self, repository, root):
        """Запомнить репозиторий и координаты корневого пакета."""
        self.repository = repository
        self.root = make_node(root.group, root.artifact, root.version)
        self.chosen = {(root.group, root.artifact): root.version}

    def name(self, node):
        """Вернуть имя пакета «группа:артефакт» без версии."""
        return node.rsplit(NODE_SEPARATOR, 1)[0]

    def make_child(self, dependency):
        """Вернуть вершину зависимости с учётом уже выбранной версии."""
        key = (dependency.group, dependency.artifact)
        version = self.chosen.setdefault(
            key, dependency.version or UNKNOWN_VERSION
        )
        return make_node(dependency.group, dependency.artifact, version)

    def fetch(self, node):
        """Получить прямые зависимости вершины.

        Ошибка для корневого пакета пробрасывается, для остальных
        выводится предупреждение, а вершина считается листом.
        """
        try:
            return get_direct_dependencies(self.repository, parse_node(node))
        except MavenError as error:
            if node == self.root:
                raise
            print(f"Предупреждение: {node}: {error}", file=sys.stderr)
            return []

    def neighbors(self, node):
        """Вернуть список вершин-зависимостей данной вершины."""
        if node.endswith(UNKNOWN_VERSION):
            return []
        dependencies = self.fetch(node)
        if node != self.root:
            dependencies = [dep for dep in dependencies
                            if is_transitive(dep)]
        return [self.make_child(dep) for dep in dependencies]
