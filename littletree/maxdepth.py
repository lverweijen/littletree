from dataclasses import dataclass


# From python 3.10, add slots=True
@dataclass(frozen=True)
class MaxDepth:
    """Limit iteration to a certain depth

    Can be passed to keep argument of methods such as tree.iter_tree().
    >>> from littletree import Node
    >>> tree = Node(identifier='root').path.create(['a', 'b', 'c', 'd']).root
    >>> [node.identifier for node in tree.iter_nodes(keep=MaxDepth(3))]
    ['root', 'a', 'b', 'c']
    """
    depth: int

    def __call__(self, _node, item):
        return item.depth <= self.depth
