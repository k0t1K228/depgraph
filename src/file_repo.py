"""Тестовый репозиторий: граф зависимостей из текстового файла."""

import re

NAME_PATTERN = re.compile(r"^[A-Z]+$")
SEPARATOR = ":"


class FileRepoError(Exception):
    """Ошибка чтения или использования файла тестового репозитория."""


def check_name(name, number):
    """Проверить, что имя пакета состоит из заглавных латинских букв."""
    if not NAME_PATTERN.match(name):
        raise FileRepoError(f"строка {number}: недопустимое имя '{name}'")


def parse_line(line, number):
    """Разобрать строку «A: B C» в пару (пакет, список зависимостей)."""
    name, separator, rest = line.partition(SEPARATOR)
    if not separator:
        raise FileRepoError(f"строка {number}: нет символа '{SEPARATOR}'")
    name = name.strip()
    children = rest.split()
    for item in [name] + children:
        check_name(item, number)
    return name, children


def parse_graph(lines):
    """Разобрать строки файла в словарь «пакет -> зависимости»."""
    graph = {}
    for number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        name, children = parse_line(line, number)
        if name in graph:
            raise FileRepoError(f"строка {number}: пакет {name} уже описан")
        graph[name] = children
    return graph


class FileRepository:
    """Источник зависимостей, описанных в файле тестового репозитория."""

    def __init__(self, graph):
        """Сохранить словарь «пакет -> список зависимостей»."""
        self.graph = graph

    @classmethod
    def from_file(cls, path):
        """Прочитать файл тестового репозитория."""
        try:
            with open(path, encoding="utf-8") as file:
                return cls(parse_graph(file))
        except (OSError, UnicodeDecodeError) as error:
            raise FileRepoError(f"не удалось прочитать {path}: {error}") \
                from error

    def require(self, root):
        """Убедиться, что корневой пакет описан в файле."""
        if root not in self.graph:
            raise FileRepoError(f"пакет {root} не найден в репозитории")

    def name(self, node):
        """Вернуть имя пакета для фильтрации."""
        return node

    def neighbors(self, node):
        """Вернуть зависимости пакета; неописанный пакет не имеет их."""
        return list(self.graph.get(node, []))
