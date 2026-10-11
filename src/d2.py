"""Текстовое представление графа зависимостей на языке диаграмм D2."""

DIRECTION_LINE = "direction: right"
ROOT_FILL = '"#cfe8ff"'
ID_PREFIX = "n"


def quote(text):
    """Оформить метку в кавычках, допустимых в D2."""
    if "'" not in text:
        return f"'{text}'"
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def format_d2(graph, root):
    """Построить строки D2: вершины с метками и рёбра между ними.

    Вершины получают короткие идентификаторы n0, n1, ..., а полное имя
    пакета записывается в метку, так как имена содержат символы ':' и '.',
    которые в D2 имеют особый смысл.
    """
    ids = {node: f"{ID_PREFIX}{index}" for index, node in enumerate(graph)}
    lines = [DIRECTION_LINE, ""]
    for node, node_id in ids.items():
        lines.append(f"{node_id}: {quote(node)}")
    lines.append(f"{ids[root]}.style.fill: {ROOT_FILL}")
    lines.append("")
    for node, children in graph.items():
        for child in children:
            lines.append(f"{ids[node]} -> {ids[child]}")
    return lines
