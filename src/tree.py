"""Вывод графа зависимостей в виде ASCII-дерева."""

from collections import deque

BRANCH = "├── "
LAST_BRANCH = "└── "
PIPE = "│   "
SPACE = "    "
CYCLE_MARK = " (цикл)"
REPEAT_MARK = " (*)"
LAST_INDEX = -1


def bfs_depths(graph, root):
    """Вычислить расстояние от корня до каждой вершины (обход в ширину)."""
    depths = {root: 0}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for child in graph.get(node, []):
            if child not in depths:
                depths[child] = depths[node] + 1
                queue.append(child)
    return depths


def child_entries(graph, node, prefix, depth):
    """Вернуть записи стека для потомков узла (в обратном порядке)."""
    children = graph.get(node, [])
    entries = [
        (child, prefix, child == children[LAST_INDEX], depth)
        for child in children
    ]
    entries.reverse()
    return entries


def classify(node, depth, path, expanded, depths):
    """Определить пометку узла и нужно ли раскрывать его потомков.

    Узел раскрывается там, где он встречается ближе всего к корню
    (как в дереве разрешённых зависимостей Maven), остальные вхождения
    помечаются (*).
    """
    if node in path:
        return CYCLE_MARK, False
    if node in expanded or depth != depths[node]:
        return REPEAT_MARK, False
    return "", True


def format_tree(graph, root):
    """Построить строки ASCII-дерева обходом в глубину без рекурсии.

    Повторное вхождение узла помечается (*) и не раскрывается, узел,
    замыкающий цикл, помечается (цикл).
    """
    depths = bfs_depths(graph, root)
    lines = [root]
    expanded = {root}
    path = [root]
    stack = child_entries(graph, root, "", 1)
    while stack:
        node, prefix, is_last, depth = stack.pop()
        del path[depth:]
        mark, expand = classify(node, depth, path, expanded, depths)
        connector = LAST_BRANCH if is_last else BRANCH
        lines.append(f"{prefix}{connector}{node}{mark}")
        if expand:
            expanded.add(node)
            path.append(node)
            extension = SPACE if is_last else PIPE
            stack.extend(
                child_entries(graph, node, prefix + extension, depth + 1)
            )
    return lines
