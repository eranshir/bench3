def iter_nodes(tree):
    """Yield ``(node_value, depth)`` pairs in depth-first order.

    A tree node is {"value": X, "children": [...]}.
    """
    node = tree
    depth = 0
    stack = []

    while True:
        yield node["value"], depth
        stack.append((iter(node.get("children", [])), depth + 1))

        while stack:
            children, child_depth = stack[-1]
            try:
                node = next(children)
            except StopIteration:
                stack.pop()
            else:
                depth = child_depth
                break
        else:
            return


def collect_values(tree):
    return [value for value, _depth in iter_nodes(tree)]


def max_depth(tree):
    return max(depth for _value, depth in iter_nodes(tree))
