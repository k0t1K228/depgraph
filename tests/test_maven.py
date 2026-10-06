"""Тесты получения и разбора зависимостей Maven."""

import unittest
import urllib.error
from unittest import mock

from src import maven
from src.pom import Coordinates, MavenError, parse_pom

REPO = "https://repo.example.org/maven2/"

CHILD_POM = b"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <parent>
    <groupId>org.demo</groupId>
    <artifactId>parent</artifactId>
    <version>1.0</version>
  </parent>
  <artifactId>child</artifactId>
  <properties><lib.version>2.5</lib.version></properties>
  <dependencies>
    <dependency>
      <groupId>org.demo</groupId>
      <artifactId>lib</artifactId>
      <version>${lib.version}</version>
    </dependency>
    <dependency>
      <groupId>org.demo</groupId>
      <artifactId>managed</artifactId>
    </dependency>
    <dependency>
      <groupId>org.demo</groupId>
      <artifactId>tools</artifactId>
      <version>${project.version}</version>
      <scope>test</scope>
      <optional>true</optional>
    </dependency>
  </dependencies>
</project>
"""

PARENT_POM = b"""<?xml version="1.0" encoding="UTF-8"?>
<project>
  <groupId>org.demo</groupId>
  <artifactId>parent</artifactId>
  <version>1.0</version>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>org.demo</groupId>
        <artifactId>managed</artifactId>
        <version>9.9</version>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.demo</groupId>
      <artifactId>inherited</artifactId>
      <version>3.0</version>
    </dependency>
  </dependencies>
</project>
"""

POMS = {
    REPO + "org/demo/child/1.0/child-1.0.pom": CHILD_POM,
    REPO + "org/demo/parent/1.0/parent-1.0.pom": PARENT_POM,
}

def fake_fetch(url):
    """Вернуть pom из словаря POMS вместо обращения к сети."""
    if url not in POMS:
        raise MavenError(f"файл не найден в репозитории: {url}")
    return POMS[url]

class MavenTest(unittest.TestCase):
    """Проверка сбора прямых зависимостей."""

    def test_pom_url(self):
        """URL pom-файла строится по правилам репозитория Maven."""
        coords = Coordinates("org.demo", "child", "1.0")
        self.assertEqual(
            maven.pom_url(REPO, coords),
            REPO + "org/demo/child/1.0/child-1.0.pom",
        )

    def test_make_coordinates(self):
        """Имя пакета разбивается на группу и артефакт."""
        coords = maven.make_coordinates("org.demo:child", "1.0")
        self.assertEqual(coords, Coordinates("org.demo", "child", "1.0"))

    def test_parse_pom_inherits_group_and_version(self):
        """Группа и версия берутся у родителя, если не заданы."""
        pom = parse_pom(CHILD_POM)
        self.assertEqual(
            pom.coordinates, Coordinates("org.demo", "child", "1.0")
        )

    def test_parse_pom_invalid_xml(self):
        """Некорректный XML приводит к MavenError."""
        with self.assertRaises(MavenError):
            parse_pom(b"<project>")

    @mock.patch("src.maven.fetch_bytes", side_effect=fake_fetch)
    def test_direct_dependencies(self, _fetch):
        """Версии, свойства и унаследованные зависимости разрешаются."""
        coords = Coordinates("org.demo", "child", "1.0")
        result = maven.get_direct_dependencies(REPO, coords)
        versions = {dep.artifact: dep.version for dep in result}
        self.assertEqual(versions, {
            "inherited": "3.0",
            "lib": "2.5",
            "managed": "9.9",
            "tools": "1.0",
        })

    @mock.patch("src.maven.fetch_bytes", side_effect=fake_fetch)
    def test_scope_and_optional(self, _fetch):
        """Область видимости и признак optional читаются из pom."""
        coords = Coordinates("org.demo", "child", "1.0")
        result = maven.get_direct_dependencies(REPO, coords)
        tools = [dep for dep in result if dep.artifact == "tools"][0]
        self.assertEqual(tools.scope, "test")
        self.assertTrue(tools.optional)

    @mock.patch("src.maven.fetch_bytes", side_effect=fake_fetch)
    def test_package_not_found(self,
_fetch):
        """Отсутствующий пакет приводит к MavenError."""
        coords = Coordinates("org.demo", "absent", "1.0")
        with self.assertRaises(MavenError):
            maven.get_direct_dependencies(REPO, coords)

    @mock.patch("urllib.request.urlopen")
    def test_http_404(self, urlopen):
        """Ответ 404 превращается в понятную ошибку."""
        urlopen.side_effect = urllib.error.HTTPError(
            REPO, maven.HTTP_NOT_FOUND, "Not Found", None, None
        )
        with self.assertRaises(MavenError):
            maven.fetch_bytes(REPO)

    @mock.patch("urllib.request.urlopen")
    def test_network_error(self, urlopen):
        """Сетевая ошибка превращается в MavenError."""
        urlopen.side_effect = urllib.error.URLError("нет сети")
        with self.assertRaises(MavenError):
            maven.fetch_bytes(REPO)
