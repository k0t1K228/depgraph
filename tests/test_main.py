"""Тесты командной строки."""

import contextlib
import io
import os
import tempfile
import unittest

from src.main import EXIT_ERROR, EXIT_OK, main

REPO_TEXT = "A: B C\nB: C\nC:\n"
CONFIG_TEXT = (
    "parameter,value\n"
    "package_name,A\n"
    "repository,{repo}\n"
    "test_mode,true\n"
    "version,1.0\n"
    "output_file,graph.png\n"
    "ascii_tree,false\n"
    "filter_substring,\n"
)


class MainTest(unittest.TestCase):
    """Проверка режимов вывода и кодов завершения."""

    def setUp(self):
        """Создать тестовый репозиторий и конфигурацию."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo = os.path.join(self.tmp.name, "repo.txt")
        self.config = os.path.join(self.tmp.name, "config.csv")
        with open(repo, "w", encoding="utf-8") as file:
            file.write(REPO_TEXT)
        with open(self.config, "w", encoding="utf-8") as file:
            file.write(CONFIG_TEXT.format(repo=repo))

    def run_main(self, *args):
        """Запустить main и вернуть код, stdout и stderr."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_graph_mode(self):
        """По умолчанию выводится граф зависимостей."""
        code, out, _ = self.run_main(self.config)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("A -> B, C", out)

    def test_load_order_mode(self):
        """Флаг --load-order выводит порядок загрузки."""
        code, out, _ = self.run_main(self.config, "--load-order")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.splitlines()[1:], ["1. C", "2. B", "3. A"])

    def test_error_exit_code(self):
        """Ошибка конфигурации даёт код EXIT_ERROR и сообщение."""
        code, _, err = self.run_main(os.path.join(self.tmp.name, "no.csv"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка", err)
