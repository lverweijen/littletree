from typing import Sequence, Mapping, TypeVar, Callable

from ..basenode import BaseNode

TNode = TypeVar("NodeType", bound=BaseNode)


class RowSerializer:
    """Serializes a tree to a list of dicts containing path and data."""
    def __init__(self, factory: Callable[[], TNode], path_name="path", fields=()):
        """
        Create path serializer. Useful to convert to/from csv-like formats.
        :param factory: How to create a node
        :param path_name: Attribute (or attributes) to store path in
        :param fields: Fields to save from node
        """
        self.factory = factory
        self.path_name = path_name
        self.fields = fields

        if path_name is None and self.fields:
            raise ValueError("path_name can not be None if fields are given")
        if not isinstance(self.fields, Sequence):
            raise TypeError("fields should be a sequence")

    def from_rows(self, rows: Sequence[Mapping]):
        factory = self.factory
        path_name = self.path_name

        root = factory()
        for row in rows:
            if path_name is None:
                path = row
            elif isinstance(path_name, str):
                path = row[path_name]
            else:
                path = [row[segment] for segment in path_name if segment in row]

            data = {field: row[field] for field in self.fields}
            parent = root.path.create(path[:-1])
            parent[path[-1]] = factory(**data)

        return root

    def to_rows(self, root: TNode, leaves_only: bool = False, path_prefix=()):
        path_name = self.path_name
        fields = self.fields

        # Check if unable to store more children
        if path_name and not isinstance(path_name, str) and len(path_prefix) == len(path_name):
            return

        for child in root.children:
            path = path_prefix + (child.identifier,)
            if path_name is None:
                row = path
            elif isinstance(path_name, str):
                row = {path_name: path}
            else:
                row = {name: segment for name, segment in zip(path_name, path)}

            for field in fields:
                row[field] = getattr(child, field)

            if not leaves_only or child.is_leaf:
                yield row
            yield from self.to_rows(child, leaves_only=leaves_only, path_prefix=path)
