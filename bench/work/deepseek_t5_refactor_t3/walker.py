def iter_nodes(tree):
    """Depth-first generator yielding (node_value, depth) tuples.

    A tree node is {"value": X, "children": [...]}.
    """
    stack = [(tree, 0)]
    while stack:
        node, depth = stack.pop()
        yield node["value"], depth
        children = node.get("children", [])
        # Push children in reverse so they are visited in original order.
        for i in range(len(children) - 1, -1, -1):
            stack.append((children[i], depth + 1))


def collect_values(tree):
    return [value for value, _ in iter_nodes(tree)]


def max_depth(tree):
    return max(depth for _, depth in iter_nodes(tree))
