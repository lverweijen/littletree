import itertools
from fnmatch import fnmatchcase
from typing import Optional, TypeVar, Iterable, Set

TNode = TypeVar("NodeType", bound="BaseNode")


class NodePath:
    __slots__ = "_node"

    # Can be overriden by child classes
    separator = "/"

    def __init__(self, node: TNode):
        self._node = node

    def __call__(self, path) -> TNode:
        if isinstance(path, str):
            path = path.split(self.separator)
        node = self._node
        for segment in path:
            node = node._cdict[segment]
        return node

    def __len__(self):
        return 1 + sum(1 for _ in self._node.iter_ancestors())

    def __iter__(self) -> Iterable[str]:
        node = self._node
        return itertools.chain(reversed(tuple(node.iter_ancestors())), [node])

    def __str__(self) -> str:
        separator = self.separator
        return separator + separator.join([node.identifier for node in self])

    def get(self, path) -> Optional[TNode]:
        try:
            return self(path)
        except KeyError:
            return None

    def create(self, path) -> TNode:
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

    def glob(self, path) -> Set[TNode]:
        """
        Find nodes by globbing patterns.

        For example to find all nodes that start with 'a':
            node.path.glob("**/a*")
        """

        if isinstance(path, str):
            path = path.split(self.separator)

        nodes = {self._node}
        for segment in path:
            if segment == "**":
                nodes = {node for candidate in nodes for node in candidate.iter_tree()}
            elif segment == "":
                nodes = {node for node in nodes if not node.is_leaf}
            elif self._is_pattern(segment):
                nodes = {node for candidate in nodes for node in candidate.children
                         if fnmatchcase(str(node.identifier), segment)}
            else:
                nodes = {candidate[segment] for candidate in nodes if segment in candidate}
        return nodes

    @staticmethod
    def _is_pattern(segment) -> bool:
        """Check if segment is a pattern. If not direct access is much faster."""
        return isinstance(segment, str) and any(char in segment for char in "*?[")
