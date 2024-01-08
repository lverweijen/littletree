import itertools
from fnmatch import fnmatchcase
from typing import Optional, TypeVar, Iterable, Iterator, Tuple

from littletree.exceptions import DifferentTreeError

TNode = TypeVar("TNode", bound="BaseNode")


class NodePath:
    __slots__ = "_node"

    # Can be overriden by child classes
    separator = "/"

    def __init__(self, node: TNode):
        """Do not instantiate directly, use node.path instead."""
        self._node = node

    def __call__(self, path) -> TNode:
        if isinstance(path, str):
            path = path.split(self.separator)
        node = self._node
        for segment in path:
            node = node._cdict[segment]
        return node

    def __eq__(self, other):
        if not isinstance(other, NodePath):
            return False
        if len(self) != len(other):
            return False
        return all(s1.identifier == s2.identifier for s1, s2 in zip(self, other))

    def __str__(self) -> str:
        separator = self.separator
        return separator + separator.join([str(node.identifier) for node in self])

    def count_nodes(self) -> int:
        """Count nodes on path."""
        return 1 + self.count_edges()

    def count_edges(self) -> int:
        """Count edges on path."""
        return self._node.count_ancestors()

    __len__ = count_nodes

    def iter_nodes(self) -> Iterator[TNode]:
        """Iterate through nodes on path."""
        node = self._node
        return itertools.chain(reversed(tuple(node.iter_ancestors())), [node])

    def iter_edges(self) -> Iterator[Tuple[TNode, TNode]]:
        """Iterate through edges on path."""
        return itertools.pairwise(self.iter_nodes())

    __iter__ = iter_nodes

    def __reversed__(self) -> Iterator[TNode]:
        node = self._node
        return itertools.chain([node], node.iter_ancestors())

    def get(self, path) -> Optional[TNode]:
        """Like calling path, but return None if node is missing."""
        try:
            return self(path)
        except KeyError:
            return None

    def create(self, path) -> TNode:
        """Like get, but create missing nodes."""
        if isinstance(path, str):
            path = path.split(self.separator)

        node = self._node
        path = iter(path)

        try:
            for segment in path:
                node = node[segment]
        except KeyError:
            node = self._create_node(identifier=segment, parent=node)

            for segment in path:
                node = self._create_node(identifier=segment, parent=node)

        return node

    def _create_node(self, identifier, parent: TNode) -> TNode:
        """Subclasses can overwrite this if the construction of a Node is different."""
        node = self._node.__class__()
        node.identifier = identifier
        node.parent = parent
        return node

    def glob(self, path) -> Iterable[TNode]:
        """
        Find nodes by globbing patterns.

        For example to find all nodes that start with 'a':
            node.path.glob("**/a*")
        """

        if isinstance(path, str):
            path = path.split(self.separator)

        nodes = {id(self._node): self._node}
        for segment in path:
            if segment == "**":
                nodes = {id(node): node
                         for candidate in nodes.values()
                         for node in candidate.iter_tree()}
            elif segment == "":
                nodes = {id(node): node
                         for node in nodes.values()
                         if not node.is_leaf}
            elif self._is_pattern(segment):
                nodes = {id(node): node
                         for candidate in nodes.values()
                         for node in candidate.children
                         if fnmatchcase(str(node.identifier), segment)}
            else:
                nodes = {id(candidate[segment]): candidate[segment]
                         for candidate in nodes.values()
                         if segment in candidate}

        return nodes.values()

    @staticmethod
    def _is_pattern(segment) -> bool:
        """Check if segment is a pattern. If not direct access is much faster."""
        return isinstance(segment, str) and any(char in segment for char in "*?[")

    def to(self, *others):
        """Return the path if nodes are in the same tree, else None"""
        from .route import Route
        try:
            return Route(self._node, *others)
        except DifferentTreeError:
            return None
