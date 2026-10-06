"""Тесты чтения и проверки конфигурации."""

import os
import tempfile
import unittest

from src.config import ConfigError, load_config

VALID = {
    "package_name": "org.apache.commons:commons-lang3",
    "repository": "https://repo.maven.apache.org/maven2",
    "test_mode": "false",
    "version": "3.14.0",
    "output_file": "graph.png",
    "ascii_tree": "true",
    "filter_substring": "test",
}

def write_config(directory, overrides=None, drop=()):
    """Создать CSV-файл конфигурации и вернуть путь к нему."""
    values = dict(VALID)
    values.update(overrides or {})
    for key in drop:
        del values[key]
    path = os.path.join(directory, "config.csv")
    with open(path, "w", encoding="utf-8") as file:
        file.write("parameter,value\n")
        for key, value in values.items():
            file.write(f"{key},{value}\n")
    return path

class ConfigTest(unittest.TestCase):
    """Проверка загрузки и валидации конфигурации."""

    def setUp(self):
        """Создать временный каталог для файлов конфигурации."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def load(self, **kwargs):
        """Записать конфигурацию и загрузить её."""
        return load_config(write_config(self.tmp.name, **kwargs))

    def assert_error(self, **kwargs):
        """Убедиться, что загрузка завершается ConfigError."""
        with self.assertRaises(ConfigError):
            self.load(**kwargs)

    def test_valid_config(self):
        """Корректный файл загружается без ошибок."""
        config = self.load()
        self.assertEqual(config.version, "3.14.0")
        self.assertTrue(config.ascii_tree)
        self.assertFalse(config.test_mode)

    def test_empty_filter_allowed(self):
        """Пустая подстрока фильтрации допустима."""
        config = self.load(overrides={"filter_substring": ""})
        self.assertEqual(config.filter_substring, "")

    def test_missing_file(self):
        """Отсутствующий файл конфигурации приводит к ошибке."""
        with self.assertRaises(ConfigError):
            load_config(os.path.join(self.tmp.name, "none.csv"))

    def test_bad_header(self):
        """Неверный заголовок CSV приводит к ошибке."""
        path = os.path.join(self.tmp.name, "bad.csv")
        with open(path, "w", encoding="utf-8") as file:
            file.write("a,b\n")
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_unknown_parameter(self):
        """Неизвестный параметр приводит к ошибке."""
        self.assert_error(overrides={"color": "red"})

    def test_missing_parameter(self):
        """Отсутствие обязательного параметра приводит к ошибке."""
        self.assert_error(drop=("version",))

    def test_bad_bool(self):
        """Недопустимое логическое значение приводит к ошибке."""
        self.assert_error(overrides={"test_mode": "maybe"})

    def test_bad_package(self):
        """Имя пакета без группы приводит к ошибке."""
        self.assert_error(overrides={"package_name": "lang3"})

    def test_bad_version(self):
        """Недопустимая версия приводит к ошибке."""
        self.assert_error(overrides={"version": "..bad"})

    def test_bad_extension(self):
        """Расширение файла изображения должно быть .png."""
        self.assert_error(overrides={"output_file": "graph.jpg"})

    def test_bad_output_directory(self):
        """Несуществующий каталог для изображения приводит к ошибке."""
        self.assert_error(overrides={"output_file": "no_dir/graph.png"})

    def test_bad_url(self):
        """URL репозитория должен начинаться с http или https."""
        self.assert_error(overrides={"repository": "ftp://example.com"})

    def test_test_mode_missing_file(self):
        """В тестовом режиме файл репозитория должен существовать."""
        self.assert_error(overrides={
            "test_mode": "true",
            "package_name": "A",
            "repository": "no_such_file.txt",
        })

    def test_test_mode_valid(self):
        """Тестовый режим с существующим файлом и именем A."""
        repo = os.path.join(self.tmp.name, "repo.txt")
        with open(repo, "w", encoding="utf-8") as file:
            file.write("A -> B\n")
        config = self.load(overrides={
            "test_mode": "true",
            "package_name": "A",
            "repository": repo,
        })
        self.assertTrue(config.test_mode)
