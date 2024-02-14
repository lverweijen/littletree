import itertools
from typing import Iterator, Tuple, TypeVar

from abstracttree import UpTree

from .exceptions import DifferentTreeError

TNode = TypeVar("TNode", bound=UpTree)


class Route:
    __slots__ = "_paths"

    def __init__(self, *nodes: TNode, check_tree=True):
        """Create a route through all nodes."""
        self._paths = [list(node.path) for node in nodes]

        if check_tree:
            path, *other_paths = self._paths
            root = path[0]
            for other_path in other_paths:
                if root != other_path[0]:
                    raise DifferentTreeError(root, other_path[0])

    def __repr__(self):
        nodes_str = ", ".join([str(path[-1].identifier) for path in self._paths])
        return f"{self.__class__.__name__}({nodes_str})"

    def count_nodes(self, index=None) -> int:
        """Count nodes on route."""
        return self.count_edges(index) + 1

    def count_edges(self, index=None) -> int:
        """Count edges on route."""
        paths = self._index_paths(index)
        s = 0
        for p1, p2 in itertools.pairwise(paths):
            s += len(p1) + len(p2) - 2 * self._common(p1, p2)
        return s

    __len__ = count_nodes

    def iter_nodes(self, index=None) -> Iterator[TNode]:
        """Iterate through nodes on route."""
        paths = self._index_paths(index)
        skip = False
        for p1, p2 in itertools.pairwise(paths):
            i = len(p1) - 1
            if skip:
                if i >= len(p2) or p1[i] != p2[i]:
                    i -= 1
                else:
                    i += 1
            if i < len(p1):
                while i >= len(p2) or p1[i] != p2[i]:
                    yield p1[i]
                    i -= 1
            while i < len(p2):
                yield p2[i]
                i += 1
            skip = True

    def iter_edges(self, index=None) -> Iterator[Tuple[TNode, TNode]]:
        """Iterate through edges on route."""
        return itertools.pairwise(self.iter_nodes(index))

    __iter__ = iter_nodes

    def __reversed__(self) -> Iterator[Tuple[TNode, TNode]]:
        return self.iter_nodes(slice(None, None, -1))

    def lca(self, index=None) -> TNode:
        """Find lowest common ancestor of nodes."""
        paths = self._index_paths(index)
        path = paths[0]
        c = self._common(*self._paths)
        return path[c - 1]

    def iter_lca(self, index=None) -> Iterator[TNode]:
        """Iterate over lowest common ancestors of nodes."""
        paths = self._index_paths(index)
        for p1, p2 in itertools.pairwise(paths):
            yield p1[self._common(p1, p2) - 1]

    def _index_paths(self, index=None):
        if index is None:
            return self._paths
        if isinstance(index, int):
            paths = self._paths
            return [paths[index], paths[index+1]]
        elif isinstance(index, slice):
            return self._paths[index]
        else:
            return [self._paths[i] for i in index]

    @staticmethod
    def _common(*seqs):
        lower = 0
        upper = min(len(seq) for seq in seqs) - 1
        seq, *other_seqs = seqs
        while upper - lower > 1:
            index = lower + (upper - lower + 1) // 2
            if all(seq[index] == other[index] for other in other_seqs):
                lower = index
            else:
                upper = index

        if all(seq[upper] == other[upper] for other in other_seqs):
            return upper + 1
        else:
            return upper
