def iter_nodes(tree):
    """Depth-first generator yielding (value, depth) tuples.

    A tree node is {"value": X, "children": [...]}. The walk is lazy and
    iterative, so it works on deep or infinite trees.
    """
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
