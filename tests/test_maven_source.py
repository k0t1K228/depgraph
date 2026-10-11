"""Тесты источника зависимостей Maven (с подменой сетевых запросов)."""

import unittest
from unittest import mock

from src.graph import build_graph
from src.maven_source import MavenSource
from src.pom import Coordinates, Dependency, MavenError

ROOT = Coordinates("g", "root", "1.0")


def dep(artifact, version="1.0", scope="compile", optional=False):
    """Создать зависимость группы g для тестов."""
    return Dependency("g", artifact, version, scope, optional)


def fake_dependencies(table):
    """Создать подмену get_direct_dependencies по таблице «артефакт»."""

    def fake(_repository, coords):
        if coords.artifact not in table:
            raise MavenError(f"нет пакета {coords.artifact}")
        return table[coords.artifact]

    return fake


class MavenSourceTest(unittest.TestCase):
    """Проверка правил выбора зависимостей Maven."""

    def build(self, table, substring=""):
        """Построить граф для корня root по таблице зависимостей."""
        source = MavenSource("https://repo", ROOT)
        target = "src.maven_source.get_direct_dependencies"
        with mock.patch(target, side_effect=fake_dependencies(table)):
            return build_graph(source.root, source, substring)

    def test_transitive_graph(self):
        """Транзитивные зависимости попадают в граф."""
        graph = self.build({"root": [dep("a")], "a": [dep("b")], "b": []})
        self.assertEqual(graph["g:a:1.0"], ["g:b:1.0"])

    def test_root_keeps_test_scope(self):
        """У корневого пакета учитываются зависимости любой области."""
        graph = self.build({"root": [dep("t", scope="test")], "t": []})
        self.assertEqual(graph["g:root:1.0"], ["g:t:1.0"])

    def test_non_root_skips_test_and_optional(self):
        """У остальных пакетов test и optional не наследуются."""
        table = {
            "root": [dep("a")],
            "a": [dep("t", scope="test"), dep("o", optional=True),
                  dep("r", scope="runtime")],
            "r": [],
        }
        graph = self.build(table)
        self.assertEqual(graph["g:a:1.0"], ["g:r:1.0"])

    def test_nearest_version_wins(self):
        """При конфликте версий выбирается ближайшая к корню."""
        table = {
            "root": [dep("a"), dep("b", version="2.0")],
            "a": [dep("b", version="1.0")],
            "b": [],
        }
        graph = self.build(table)
        self.assertEqual(graph["g:a:1.0"], ["g:b:2.0"])

    def test_cycle_through_root(self):
        """Цикл, возвращающий к корню, не зацикливает обход."""
        graph = self.build({"root": [dep("a")], "a": [dep("root")]})
        self.assertEqual(graph["g:a:1.0"], ["g:root:1.0"])

    def test_filter_by_package_name(self):
        """Фильтр сравнивается с «группа:артефакт», а не с версией."""
        table = {"root": [dep("skip", version="9.9"), dep("keep")],
                 "keep": []}
        graph = self.build(table, substring="skip")
        self.assertEqual(graph["g:root:1.0"], ["g:keep:1.0"])

    def test_unresolved_version_is_leaf(self):
        """Зависимость без версии остаётся листом."""
        graph = self.build({"root": [dep("a", version="")]})
        self.assertEqual(graph["g:a:?"], [])

    def test_non_root_error_is_soft(self):
        """Ошибка загрузки не корневого пакета делает его листом."""
        with mock.patch("sys.stderr"):
            graph = self.build({"root": [dep("missing")]})
        self.assertEqual(graph["g:missing:1.0"], [])

    def test_root_error_raises(self):
        """Ошибка загрузки корневого пакета пробрасывается."""
        with self.assertRaises(MavenError):
            self.build({})
