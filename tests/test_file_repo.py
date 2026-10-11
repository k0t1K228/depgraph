"""Тесты чтения файла тестового репозитория."""

import os
import tempfile
import unittest

from src.file_repo import FileRepoError, FileRepository, parse_graph


class ParseGraphTest(unittest.TestCase):
    """Проверка разбора строк файла."""

    def test_valid(self):
        """Корректное описание разбирается в словарь."""
        graph = parse_graph(["A: B C", "", "B:", "C: B"])
        self.assertEqual(graph, {"A": ["B", "C"], "B": [], "C": ["B"]})

    def test_missing_separator(self):
        """Строка без двоеточия приводит к ошибке."""
        with self.assertRaises(FileRepoError):
            parse_graph(["A B"])

    def test_lowercase_name(self):
        """Имя не из заглавных латинских букв приводит к ошибке."""
        with self.assertRaises(FileRepoError):
            parse_graph(["A: b"])

    def test_duplicate_package(self):
        """Повторное описание пакета приводит к ошибке."""
        with self.assertRaises(FileRepoError):
            parse_graph(["A: B", "A: C"])


class FileRepositoryTest(unittest.TestCase):
    """Проверка чтения файла и поиска корня."""

    def test_from_file(self):
        """Файл читается в FileRepository."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "repo.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write("A: B\nB:\n")
            repository = FileRepository.from_file(path)
        self.assertEqual(repository.neighbors("A"), ["B"])

    def test_missing_file(self):
        """Отсутствующий файл приводит к ошибке."""
        with self.assertRaises(FileRepoError):
            FileRepository.from_file("no_such_repo.txt")

    def test_require_missing_root(self):
        """Корневой пакет должен быть описан в файле."""
        with self.assertRaises(FileRepoError):
            FileRepository({"A": []}).require("Z")
