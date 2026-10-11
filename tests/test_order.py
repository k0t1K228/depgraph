"""Тесты вычисления порядка загрузки зависимостей."""

import unittest

from src.order import compute_load_order, format_order


class LoadOrderTest(unittest.TestCase):
    """Проверка порядка загрузки и обработки циклов."""

    def test_single_package(self):
        """Пакет без зависимостей загружается сам."""
        self.assertEqual(compute_load_order({"A": []}, "A"), (["A"], []))

    def test_chain(self):
        """Цепочка загружается от самой глубокой зависимости."""
        graph = {"A": ["B"], "B": ["C"], "C": []}
        order, cycles = compute_load_order(graph, "A")
        self.assertEqual(order, ["C", "B", "A"])
        self.assertEqual(cycles, [])

    def test_declaration_order(self):
        """Независимые зависимости идут в порядке объявления."""
        graph = {"A": ["B", "C"], "B": [], "C": []}
        self.assertEqual(compute_load_order(graph, "A")[0],
                         ["B", "C", "A"])

    def test_diamond(self):
        """Общая зависимость загружается один раз и раньше потребителей."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        order, _ = compute_load_order(graph, "A")
        self.assertEqual(order, ["D", "B", "C", "A"])

    def test_dependencies_before_dependents(self):
        """В графе без циклов зависимость всегда раньше пакета."""
        graph = {"A": ["B", "C"], "B": ["D", "E"], "C": ["E"],
                 "D": [], "E": ["F"], "F": []}
        order, _ = compute_load_order(graph, "A")
        for node, children in graph.items():
            for child in children:
                self.assertLess(order.index(child), order.index(node))

    def test_cycle(self):
        """Ребро, замыкающее цикл, пропускается и сообщается."""
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        order, cycles = compute_load_order(graph, "A")
        self.assertEqual(order, ["C", "B", "A"])
        self.assertEqual(cycles, [("C", "A")])

    def test_self_loop(self):
        """Зависимость пакета от самого себя считается циклом."""
        graph = {"A": ["A", "B"], "B": []}
        order, cycles = compute_load_order(graph, "A")
        self.assertEqual(order, ["B", "A"])
        self.assertEqual(cycles, [("A", "A")])

    def test_every_package_once(self):
        """Каждый пакет встречается в порядке ровно один раз."""
        graph = {"A": ["B", "C"], "B": ["C"], "C": ["A", "D"], "D": []}
        order, _ = compute_load_order(graph, "A")
        self.assertEqual(sorted(order), sorted(graph))

    def test_format_order(self):
        """Порядок и циклы выводятся пронумерованным списком."""
        lines = format_order(["B", "A"], [("B", "A")])
        self.assertEqual(lines[1:3], ["1. B", "2. A"])
        self.assertEqual(lines[-1], "  B -> A")
