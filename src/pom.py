"""Разбор файла pom.xml в удобные структуры данных."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

DEFAULT_SCOPE = "compile"
BOOL_TRUE = "true"

class MavenError(Exception):
    """Ошибка получения или разбора данных Maven."""

@dataclass(frozen=True)
class Coordinates:
    """Координаты артефакта Maven."""

    group: str
    artifact: str
    version: str

@dataclass
class Dependency:
    """Зависимость, объявленная в pom.xml."""

    group: str
    artifact: str
    version: str
    scope: str
    optional: bool

@dataclass
class Pom:
    """Содержимое одного pom.xml."""

    coordinates: Coordinates
    parent: Coordinates | None
    properties: dict
    managed: dict
    dependencies: list

def strip_namespaces(root):
    """Убрать пространства имён из тегов, чтобы упростить поиск."""
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]

def text_of(element, name):
    """Вернуть текст дочернего элемента или пустую строку."""
    child = element.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()

def parse_parent(root):
    """Прочитать блок parent, если он есть."""
    parent = root.find("parent")
    if parent is None:
        return None
    return Coordinates(
        text_of(parent, "groupId"),
        text_of(parent, "artifactId"),
        text_of(parent, "version"),
    )

def parse_properties(root):
    """Прочитать блок properties в словарь «имя -> значение»."""
    node = root.find("properties")
    if node is None:
        return {}
    return {child.tag: (child.text or "").strip() for child in node}

def parse_dependency(node):
    """Преобразовать элемент dependency в объект Dependency."""
    return Dependency(
        group=text_of(node, "groupId"),
        artifact=text_of(node, "artifactId"),
        version=text_of(node, "version"),
        scope=text_of(node, "scope") or DEFAULT_SCOPE,
        optional=text_of(node, "optional").lower() == BOOL_TRUE,
    )

def parse_dependencies(node):
    """Прочитать все dependency внутри узла dependencies."""
    if node is None:
        return []
    return [parse_dependency(item) for item in node.findall("dependency")]

def parse_managed(root):
    """Прочитать dependencyManagement: «(группа, артефакт) -> версия»."""
    node = root.find("dependencyManagement/dependencies")
    managed = {}
    for dependency in parse_dependencies(node):
        managed[(dependency.group, dependency.artifact)] = dependency.version
    return managed

def parse_pom(content):
    """Разобрать содержимое pom.xml (bytes) в объект Pom."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        raise MavenError(f"некорректный pom.xml: {error}") from error
    strip_namespaces(root)
    parent = parse_parent(root)
    group = text_of(root, "groupId") or (parent.group if parent else "")
    version = text_of(root, "version") or (parent.version if parent else "")
    return Pom(
        coordinates=Coordinates(group, text_of(root, "artifactId"), version),
        parent=parent,
        properties=parse_properties(root),
        managed=parse_managed(root),
        dependencies=parse_dependencies(root.find("dependencies")),
    )
