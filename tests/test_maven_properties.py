"""Тесты подстановки встроенных свойств проекта в pom.xml."""

import unittest
from unittest import mock

from src import maven
from src.pom import Coordinates

REPO = "https://repo.example.org/maven2"

POM_TEMPLATE = b"""<project>
  <groupId>org.demo</groupId>
  <artifactId>tck</artifactId>
  <version>1</version>
  <dependencies>
    <dependency>
      <groupId>${PREFIX.groupId}</groupId>
      <artifactId>inject</artifactId>
      <version>${PREFIX.version}</version>
    </dependency>
  </dependencies>
</project>
"""


class ProjectPropertiesTest(unittest.TestCase):
    """Проверка свойств project.* и устаревших псевдонимов pom.*."""

    def resolve(self, prefix):
        """Получить зависимость пакета, использующего заданный префикс."""
        content = POM_TEMPLATE.replace(b"PREFIX", prefix.encode())
        coords = Coordinates("org.demo", "tck", "1")
        with mock.patch("src.maven.fetch_bytes", return_value=content):
            return maven.get_direct_dependencies(REPO, coords)[0]

    def test_pom_prefix(self):
        """Псевдоним pom.* заменяется значениями пакета."""
        dependency = self.resolve("pom")
        self.assertEqual(dependency.group, "org.demo")
        self.assertEqual(dependency.version, "1")

    def test_project_prefix(self):
        """Свойства project.* заменяются значениями пакета."""
        dependency = self.resolve("project")
        self.assertEqual(dependency.group, "org.demo")
        self.assertEqual(dependency.version, "1")
