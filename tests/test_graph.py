"""Тесты построения графа зависимостей обходом в ширину."""

import unittest

from src.file_repo import FileRepository
from src.graph import build_graph, format_graph


def graph_of(description, root="A", substring=""):
    """Построить граф для тестового репозитория из словаря."""
    return build_graph(root, FileRepository(description), substring)


class GraphTest(unittest.TestCase):
    """Проверка BFS, фильтрации и обработки циклов."""

    def test_chain(self):
        """Линейная цепочка зависимостей."""
        graph = graph_of({"A": ["B"], "B": ["C"], "C": []})
        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": []})

    def test_bfs_order(self):
        """Вершины обходятся по уровням, а не в глубину."""
        description = {"A": ["B", "C"], "B": ["D"], "C": ["E"],
                       "D": [], "E": []}
        self.assertEqual(list(graph_of(description)),
                         ["A", "B", "C", "D", "E"])

    def test_diamond_visits_node_once(self):
        """Общая зависимость попадает в граф один раз."""
        description = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        graph = graph_of(description)
        self.assertEqual(len(graph), len(description))
        self.assertEqual(graph["D"], [])

    def test_cycle(self):
        """Цикл не приводит к бесконечному обходу."""
        graph = graph_of({"A": ["B"], "B": ["C"], "C": ["A"]})
        self.assertEqual(graph["C"], ["A"])
        self.assertEqual(len(graph), 3)

    def test_self_loop(self):
        """Зависимость пакета от самого себя обрабатывается."""
        graph = graph_of({"A": ["A", "B"], "B": []})
        self.assertEqual(graph["A"], ["A", "B"])

    def test_unknown_package_is_leaf(self):
        """Пакет, не описанный в файле, не имеет зависимостей."""
        graph = graph_of({"A": ["X"]})
        self.assertEqual(graph, {"A": ["X"], "X": []})

    def test_duplicates_removed(self):
        """Повторы в списке зависимостей убираются."""
        graph = graph_of({"A": ["B", "B"], "B": []})
        self.assertEqual(graph["A"], ["B"])

    def test_filter_excludes_package_and_subtree(self):
        """Отфильтрованный пакет и его поддерево не анализируются."""
        description = {"A": ["B", "C"], "B": ["D"], "C": ["E"],
                       "D": [], "E": []}
        graph = graph_of(description, substring="B")
        self.assertEqual(graph, {"A": ["C"], "C": ["E"], "E": []})

    def test_filter_by_substring(self):
        """Фильтр срабатывает, если имя содержит подстроку."""
        description = {"A": ["AB", "BC", "CD"], "AB": [], "BC": [],
                       "CD": []}
        graph = graph_of(description, substring="B")
        self.assertEqual(graph["A"], ["CD"])

    def test_filter_keeps_package_reachable_other_way(self):
        """Пакет остаётся в графе, если имя не содержит подстроку."""
        graph = graph_of({"A": ["B", "C"], "B": [], "C": []}, substring="C")
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_empty_filter_excludes_nothing(self):
        """Пустая подстрока ничего не исключает."""
        graph = graph_of({"A": ["B"], "B": []}, substring="")
        self.assertEqual(len(graph), 2)

    def test_root_is_not_filtered(self):
        """Корневой пакет не фильтруется."""
        graph = graph_of({"A": ["B"], "B": []}, substring="A")
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_format_graph(self):
        """Граф выводится построчно в формате «вершина -> зависимости»."""
        lines = format_graph({"A": ["B"], "B": []})
        self.assertEqual(lines[1:], ["A -> B", "B -> (нет)"])
