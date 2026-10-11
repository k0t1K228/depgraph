"""Построение графа зависимостей обходом в ширину (BFS)."""

from collections import deque

EMPTY_MARK = "(нет)"


def is_excluded(name, substring):
    """Проверить, содержит ли имя пакета подстроку для фильтрации."""
    return bool(substring) and substring in name


def unique(items):
    """Убрать повторы из последовательности, сохранив порядок."""
    return list(dict.fromkeys(items))


def build_graph(root, source, substring):
    """Построить граф зависимостей обходом в ширину без рекурсии.

    Возвращает словарь «вершина -> список зависимостей». Пакеты, имя
    которых содержит substring, не анализируются. Повторно встреченные
    вершины (в том числе при циклах) повторно не обрабатываются.
    """
    graph = {}
    queue = deque([root])
    seen = {root}
    while queue:
        node = queue.popleft()
        children = unique(
            child for child in source.neighbors(node)
            if not is_excluded(source.name(child), substring)
        )
        graph[node] = children
        for child in children:
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return graph


def format_graph(graph):
    """Представить граф списком строк «вершина -> зависимости»."""
    lines = [f"Граф зависимостей (BFS), вершин: {len(graph)}"]
    for node, children in graph.items():
        targets = ", ".join(children) if children else EMPTY_MARK
        lines.append(f"{node} -> {targets}")
    return lines
