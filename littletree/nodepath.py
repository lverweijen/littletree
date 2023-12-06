import itertools
from fnmatch import fnmatchcase
from typing import Optional, TypeVar, Iterable, Iterator

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

    def __len__(self):
        return 1 + sum(1 for _ in self._node.iter_ancestors())

    def __iter__(self) -> Iterator[TNode]:
        return self._node.iter_path()

    def __str__(self) -> str:
        separator = self.separator
        return separator + separator.join([str(node.identifier) for node in self])

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

    def to(self, other) -> Optional["PathTo"]:
        """Return the path if nodes are in the same tree, else None"""
        s_path, o_path = tuple(self), tuple(other.path)

        n_common = 0
        n_max = min(len(s_path), len(o_path))
        while n_common < n_max and s_path[n_common] == o_path[n_common]:
            n_common += 1

        if n_common:
            return PathTo(s_path, o_path, n_common)


class PathTo:
    __slots__ = "_path1", "_path2", "_ncommon"

    def __init__(self, path1, path2, n_common):
        """Do not instantiate directly. Use node1.path.to(node2) instead."""
        self._path1 = path1
        self._path2 = path2
        self._ncommon = n_common

    def __iter__(self) -> Iterator[TNode]:
        n_common = self._ncommon
        n_up = len(self._path1) - n_common
        up = itertools.islice(reversed(self._path1), n_up)
        down = itertools.islice(self._path2, n_common - 1, None)
        return itertools.chain(up, down)

    def __reversed__(self) -> Iterable[TNode]:
        n_common = self._ncommon
        n_up = len(self._path2) - n_common
        up = itertools.islice(reversed(self._path2), n_up)
        down = itertools.islice(self._path1, n_common - 1, None)
        return itertools.chain(up, down)

    def __len__(self):
        return len(self._path1) + len(self._path2) - 2 * self._ncommon + 1

    def __str__(self):
        sep = self.lca.path.separator
        output = []
        n_up = len(self._path1) - self._ncommon
        down = itertools.islice(self._path2, self._ncommon, None)
        output.extend(n_up * [".."])
        output.extend([node.identifier for node in down])
        return sep.join(output)

    @property
    def lca(self) -> TNode:
        """Find the lowest common ancestor of both nodes."""
        return self._path1[self._ncommon - 1]
