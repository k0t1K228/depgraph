"""Тесты текстового представления графа на языке D2."""

import unittest

from src.d2 import format_d2, quote


class D2Test(unittest.TestCase):
    """Проверка генерации текста D2."""

    def test_nodes_and_edges(self):
        """Вершины получают метки, рёбра идут между идентификаторами."""
        lines = format_d2({"A": ["B"], "B": []}, "A")
        self.assertIn("n0: 'A'", lines)
        self.assertIn("n1: 'B'", lines)
        self.assertIn("n0 -> n1", lines)

    def test_root_is_highlighted(self):
        """Корневая вершина выделяется цветом."""
        lines = format_d2({"A": ["B"], "B": []}, "A")
        self.assertIn('n0.style.fill: "#cfe8ff"', lines)

    def test_maven_name_in_label(self):
        """Имя пакета Maven попадает в метку целиком, в кавычках."""
        name = "com.google.guava:guava:32.1.3-jre"
        lines = format_d2({name: []}, name)
        self.assertIn(f"n0: '{name}'", lines)

    def test_cycle_edges(self):
        """Рёбра циклов и петли записываются как обычные рёбра."""
        lines = format_d2({"A": ["A", "B"], "B": ["A"]}, "A")
        self.assertIn("n0 -> n0", lines)
        self.assertIn("n1 -> n0", lines)

    def test_quote_with_apostrophe(self):
        """Метка с апострофом оформляется двойными кавычками."""
        self.assertEqual(quote("it's"), '"it\'s"')
        self.assertEqual(quote('a"b\'c'), '"a\\"b\'c"')
