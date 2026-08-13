def iter_nodes(tree):
    """Yield ``(node_value, depth)`` pairs in depth-first order.

    A tree node is {"value": X, "children": [...]}.
    """
    stack = [(iter((tree,)), 0)]
    while stack:
        nodes, depth = stack[-1]
        try:
            node = next(nodes)
        except StopIteration:
            stack.pop()
            continue

        yield node["value"], depth
        stack.append((iter(node.get("children", [])), depth + 1))


def collect_values(tree):
    return [value for value, _ in iter_nodes(tree)]


def max_depth(tree):
    return max(depth for _, depth in iter_nodes(tree))
