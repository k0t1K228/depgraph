"""Тесты вывода графа в виде ASCII-дерева."""

import unittest

from src.tree import format_tree


class TreeTest(unittest.TestCase):
    """Проверка форматирования дерева, повторов и циклов."""

    def test_single_node(self):
        """Пакет без зависимостей выводится одной строкой."""
        self.assertEqual(format_tree({"A": []}, "A"), ["A"])

    def test_chain(self):
        """Цепочка выводится с отступами."""
        graph = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(format_tree(graph, "A"), [
            "A",
            "└── B",
            "    └── C",
        ])

    def test_branches(self):
        """Не последний потомок рисуется веткой и вертикальной чертой."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        self.assertEqual(format_tree(graph, "A"), [
            "A",
            "├── B",
            "│   └── D",
            "└── C",
        ])

    def test_repeated_node_marked(self):
        """Повторный узел помечается и не раскрывается."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"],
                 "E": []}
        self.assertEqual(format_tree(graph, "A"), [
            "A",
            "├── B",
            "│   └── D",
            "│       └── E",
            "└── C",
            "    └── D (*)",
        ])

    def test_cycle_marked(self):
        """Узел, замыкающий цикл, помечается."""
        graph = {"A": ["B"], "B": ["A"]}
        self.assertEqual(format_tree(graph, "A"), [
            "A",
            "└── B",
            "    └── A (цикл)",
        ])

    def test_self_loop(self):
        """Зависимость от самого себя считается циклом."""
        self.assertEqual(format_tree({"A": ["A"]}, "A"), [
            "A",
            "└── A (цикл)",
        ])

    def test_deep_chain_without_recursion(self):
        """Очень глубокая цепочка не вызывает переполнение рекурсии."""
        size = 5000
        graph = {str(index): [str(index + 1)] for index in range(size)}
        graph[str(size)] = []
        self.assertEqual(len(format_tree(graph, "0")), size + 1)

    def test_node_expanded_at_nearest_occurrence(self):
        """Узел раскрывается там, где он ближе всего к корню."""
        graph = {"A": ["B", "C"], "B": ["D"], "D": ["E"], "C": ["E"],
                 "E": ["F"], "F": []}
        self.assertEqual(format_tree(graph, "A"), [
            "A",
            "├── B",
            "│   └── D",
            "│       └── E (*)",
            "└── C",
            "    └── E",
            "        └── F",
        ])
