def iter_nodes(tree):
    """Depth-first preorder walk, yielding (node_value, depth) tuples.

    A tree node is {"value": X, "children": [...]}.  Iterative and lazy:
    nodes are produced one at a time without building a full list.
    """
    stack = [(tree, 0)]
    while stack:
        node, depth = stack.pop()
        yield node["value"], depth
        # Push children in reverse so they are visited in original order.
        for child in reversed(node.get("children", [])):
            stack.append((child, depth + 1))


def collect_values(tree):
    return [value for value, _ in iter_nodes(tree)]


def max_depth(tree):
    return max(depth for _, depth in iter_nodes(tree))
