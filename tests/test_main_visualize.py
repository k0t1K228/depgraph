"""Тесты режимов вывода и визуализации в командной строке."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from src.main import EXIT_ERROR, EXIT_OK, main
from src.render import RenderError

REPO_TEXT = "A: B C\nB: C\nC:\n"
CONFIG_TEXT = (
    "parameter,value\n"
    "package_name,A\n"
    "repository,{repo}\n"
    "test_mode,true\n"
    "version,1.0\n"
    "output_file,{image}\n"
    "ascii_tree,{tree}\n"
    "filter_substring,\n"
)


class VisualizeTest(unittest.TestCase):
    """Проверка ASCII-дерева и вызова визуализации."""

    def setUp(self):
        """Создать тестовый репозиторий во временном каталоге."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = os.path.join(self.tmp.name, "repo.txt")
        self.image = os.path.join(self.tmp.name, "graph.png")
        with open(self.repo, "w", encoding="utf-8") as file:
            file.write(REPO_TEXT)

    def make_config(self, tree):
        """Создать конфигурацию с заданным значением ascii_tree."""
        path = os.path.join(self.tmp.name, "config.csv")
        text = CONFIG_TEXT.format(repo=self.repo, image=self.image, tree=tree)
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def run_main(self, *args):
        """Запустить main и вернуть код, stdout и stderr."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_ascii_tree_enabled(self):
        """При ascii_tree=true выводится дерево."""
        code, out, _ = self.run_main(self.make_config("true"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("├── B", out)
        self.assertIn("C (*)", out)

    def test_ascii_tree_disabled(self):
        """При ascii_tree=false выводится список рёбер."""
        _, out, _ = self.run_main(self.make_config("false"))
        self.assertIn("A -> B, C", out)
        self.assertNotIn("├──", out)

    @mock.patch("src.main.save_diagram", return_value="graph.d2")
    def test_visualize_flag(self, save):
        """Флаг --visualize сохраняет диаграмму и сообщает о файлах."""
        code, out, _ = self.run_main(self.make_config("false"), "--visualize")
        self.assertEqual(code, EXIT_OK)
        save.assert_called_once()
        self.assertIn("Диаграмма D2: graph.d2", out)
        self.assertIn(f"Изображение: {self.image}", out)

    @mock.patch("src.main.save_diagram")
    def test_no_visualize_by_default(self, save):
        """Без флага --visualize диаграмма не создаётся."""
        self.run_main(self.make_config("false"))
        save.assert_not_called()

    @mock.patch("src.main.save_diagram", side_effect=RenderError("нет d2"))
    def test_render_error(self, _save):
        """Ошибка отрисовки даёт код EXIT_ERROR и сообщение."""
        code, _, err = self.run_main(self.make_config("false"), "--visualize")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("нет d2", err)
