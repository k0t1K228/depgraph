"""Порядок загрузки зависимостей: пакет идёт после своих зависимостей."""

ORDER_TITLE = "Порядок загрузки зависимостей"
CYCLE_TITLE = "Циклические зависимости (ребро пропущено):"


def compute_load_order(graph, root):
    """Вычислить порядок загрузки без рекурсии (обход в глубину).

    Возвращает пару (порядок, обратные рёбра). Каждый пакет попадает в
    порядок после всех своих зависимостей, корневой пакет идёт последним.
    Ребро, замыкающее цикл, пропускается и возвращается во втором списке.
    """
    order = []
    cycles = []
    done = set()
    path = {root}
    stack = [(root, iter(graph.get(root, [])))]
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            stack.pop()
            path.discard(node)
            done.add(node)
            order.append(node)
        elif child in path:
            cycles.append((node, child))
        elif child not in done:
            path.add(child)
            stack.append((child, iter(graph.get(child, []))))
    return order, cycles


def format_order(order, cycles):
    """Представить порядок загрузки списком строк."""
    lines = [f"{ORDER_TITLE} (пакетов: {len(order)}):"]
    for index, node in enumerate(order, start=1):
        lines.append(f"{index}. {node}")
    if cycles:
        lines.append(CYCLE_TITLE)
        lines.extend(f"  {node} -> {child}" for node, child in cycles)
    return lines
