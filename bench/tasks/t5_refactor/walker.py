def walk(tree, visit):
    """Depth-first walk, calling visit(node_value, depth) on each node.

    A tree node is {"value": X, "children": [...]}.
    """
    def _go(node, depth):
        visit(node["value"], depth)
        for child in node.get("children", []):
            _go(child, depth + 1)

    _go(tree, 0)


def collect_values(tree):
    out = []
    walk(tree, lambda v, d: out.append(v))
    return out


def max_depth(tree):
    seen = []
    walk(tree, lambda v, d: seen.append(d))
    return max(seen)
