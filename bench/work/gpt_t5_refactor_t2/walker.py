def iter_nodes(tree):
    """Yield ``(node_value, depth)`` pairs in depth-first order."""
    stack = [(tree, 0)]

    while stack:
        node, depth = stack.pop()
        yield node["value"], depth

        children = node.get("children", [])
        for child in reversed(children):
            stack.append((child, depth + 1))


def collect_values(tree):
    return [value for value, _ in iter_nodes(tree)]


def max_depth(tree):
    return max(depth for _, depth in iter_nodes(tree))
