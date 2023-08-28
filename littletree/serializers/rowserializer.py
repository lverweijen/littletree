from typing import Sequence, Mapping, TypeVar, Callable

from ..basenode import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)


class RowSerializer:
    """Serializes a tree to a list of dicts containing path and data."""
    def __init__(self, factory: Callable[[], TNode] = None, path_name="path", fields=()):
        """
        Create path serializer. Useful to convert to/from csv-like formats.
        :param factory: How to create a node
        :param path_name: Attribute (or attributes) to store path in
        :param fields: Fields to save from node
        """
        if factory is None:
            from ..node import Node
            factory = Node

        self.factory = factory
        self.path_name = path_name
        self.fields = fields

        if path_name is None and self.fields:
            raise ValueError("path_name can not be None if fields are given")
        if not isinstance(self.fields, Sequence):
            raise TypeError("fields should be a sequence")

    def from_rows(self, rows: Sequence[Mapping], root=None):
        factory = self.factory
        path_name = self.path_name
        fields = self.fields

        # Special case for pandas data frame (and similar apis)
        if hasattr(rows, "itertuples") and hasattr(rows, "to_dict"):
            if path_name is None:
                rows = rows.itertuples(index=False)
            else:
                rows = rows.to_dict("records")

        if root is None:
            root = factory()
        for row in rows:
            if path_name is None:
                path = row
            elif isinstance(path_name, str):
                path = row[path_name]
                if isinstance(path, str):
                    path = path.split(root.path.separator)
            else:
                path = [row[segment] for segment in path_name if segment in row]

            parent = root.path.create(path[:-1])
            node = parent[path[-1]] = factory()

            if fields:
                if isinstance(fields, str):
                    data = {}
                    for field, value in row.items():
                        if field != path_name:
                            data[field] = value
                    node.data = data
                else:
                    for field in fields:
                        setattr(node, field, row[field])


        return root

    def to_rows(self, tree: TNode, leaves_only: bool = False, path_prefix=()):
        path_name = self.path_name
        fields = self.fields

        # Check if unable to store more children
        if path_name and not isinstance(path_name, str) and len(path_prefix) == len(path_name):
            return

        for child in tree.children:
            path = path_prefix + (child.identifier,)
            if path_name is None:
                row = path
            elif isinstance(path_name, str):
                row = {path_name: path}
            else:
                row = {name: segment for name, segment in zip(path_name, path)}

            if fields:
                if isinstance(fields, str):
                    data = getattr(child, fields)
                    if data:
                        row.update(data)
                else:
                    row.update({field: getattr(child, field) for field in fields})

            if not leaves_only or child.is_leaf:
                yield row
            yield from self.to_rows(child, leaves_only=leaves_only, path_prefix=path)
