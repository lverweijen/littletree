from fnmatch import fnmatchcase
from typing import Optional, TypeVar, Set, Iterable

NodeType = TypeVar("NodeType", bound="Node")


class NodePath:
    __slots__ = "_node"

    def __init__(self, node: NodeType):
        self._node = node

    def __call__(self, *path) -> "Node":
        node = self._node
        for segment in path:
            node = node[segment]

        return node

    def __iter__(self) -> Iterable[str]:
        return (segment.identifier for segment in self._node.iter_path())

    def __str__(self) -> str:
        return "/" + "/".join(tuple(self))

    def get(self, *path) -> Optional[NodeType]:
        try:
            return self(*path)
        except KeyError:
            return None

    def create(self, *path, factory=None) -> NodeType:
        if factory is None:
            factory = self._node.__class__

        node = self._node
        path = iter(path)

        try:
            for segment in path:
                node = node[segment]
        except KeyError:
            node = factory(identifier=segment, parent=node)

            for segment in path:
                node = factory(identifier=segment, parent=node)

        return node

    def glob(self, path_str, separator="/") -> Set[NodeType]:
        """
        Find nodes by globbing patterns.
        This only works if all the nodes have a string identifier.

        If path_string starts with separator, start from root.
        Otherwise, start from self.
        """
        segments = path_str.split(separator)

        if len(segments) >= 2 and not segments[0]:
            root = self.root
            root_candidate = segments[1]

            if root_candidate == root.identifier:
                nodes = {root}
                segments = segments[2:]
            else:
                raise ValueError(f"Root is {root.identifier}, not {root_candidate}")
        else:
            nodes = {self._node}

        for segment in segments:
            if segment in (".", ""):
                continue
            elif segment == "..":
                nodes = {candidate.parent for candidate in nodes
                         if not candidate.is_root}
            elif segment == "**":
                nodes = {node for candidate in nodes
                         for node in candidate.iter_tree()}
            elif self._is_pattern(segment):
                nodes = {node for candidate in nodes
                         for node in candidate.children
                         if fnmatchcase(node.identifier, segment)}
            else:
                nodes = {candidate[segment] for candidate in nodes
                         if segment in candidate}

        return nodes

    @staticmethod
    def _is_pattern(path) -> bool:
        """Check if path is a pattern. If not direct access is much faster."""
        return any(char in path for char in "*?[")
