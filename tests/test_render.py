"""Тесты сохранения диаграммы и вызова утилиты d2."""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from src import render
from src.render import RenderError


def completed(returncode=0, stderr=""):
    """Создать подмену результата subprocess.run."""
    return SimpleNamespace(returncode=returncode, stderr=stderr)


class RenderTest(unittest.TestCase):
    """Проверка записи D2 и запуска отрисовки."""

    def setUp(self):
        """Создать временный каталог."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.image = os.path.join(self.tmp.name, "graph.png")

    def test_d2_path(self):
        """Файл D2 лежит рядом с изображением."""
        self.assertEqual(render.d2_path_for("out/graph.png"), "out/graph.d2")

    def test_save_text(self):
        """Текст диаграммы записывается в файл."""
        path = os.path.join(self.tmp.name, "a.d2")
        render.save_text(path, ["x -> y"])
        with open(path, encoding="utf-8") as file:
            self.assertEqual(file.read(), "x -> y\n")

    def test_save_text_error(self):
        """Ошибка записи превращается в RenderError."""
        with self.assertRaises(RenderError):
            render.save_text(os.path.join(self.tmp.name, "no", "a.d2"), ["x"])

    @mock.patch("src.render.shutil.which", return_value=None)
    def test_d2_not_installed(self, _which):
        """Отсутствие утилиты d2 приводит к понятной ошибке."""
        with self.assertRaises(RenderError):
            render.render_png("a.d2", self.image)

    @mock.patch("src.render.subprocess.run", return_value=completed())
    @mock.patch("src.render.shutil.which", return_value="/usr/bin/d2")
    def test_render_called(self, _which, run):
        """Утилита вызывается с файлом D2 и именем изображения."""
        render.render_png("a.d2", self.image)
        command = run.call_args[0][0]
        self.assertEqual(command, ["/usr/bin/d2", "a.d2", self.image])

    @mock.patch("src.render.subprocess.run")
    @mock.patch("src.render.shutil.which", return_value="/usr/bin/d2")
    def test_d2_failure(self, _which, run):
        """Ненулевой код возврата d2 приводит к ошибке с её сообщением."""
        run.return_value = completed(returncode=1, stderr="bad syntax")
        with self.assertRaises(RenderError) as context:
            render.render_png("a.d2", self.image)
        self.assertIn("bad syntax", str(context.exception))

    @mock.patch("src.render.render_png")
    def test_save_diagram(self, render_png):
        """Диаграмма сохраняется, затем запускается отрисовка."""
        d2_path = render.save_diagram(["x -> y"], self.image)
        self.assertTrue(os.path.isfile(d2_path))
        render_png.assert_called_once_with(d2_path, self.image)
