import itertools
from typing import Sequence, Mapping, TypeVar, Callable, Union, Optional

from ._nodeeditor import get_editor
from ..basenode import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)


class RowSerializer:
    __slots__ = "path_name", "sep", "factory", "editor"
    """Serializes a tree to a list of dicts containing path and data."""
    def __init__(
        self,
        factory: Callable[[], TNode] = None,
        path_name: Union[str, Sequence[str], None] = "path",
        sep: Optional[str] = "/",
        fields: Sequence[str] = (),
        data_field: str = None
    ):
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
        self.sep = sep
        self.editor = get_editor(fields, data_field)

        if path_name is None and fields:
            raise ValueError("path_name can not be None if fields are given")
        if not isinstance(fields, Sequence):
            raise TypeError("fields should be a sequence")

    def from_rows(self, rows: Sequence[Mapping], root=None):
        factory = self.factory
        path_name = self.path_name
        sep = self.sep
        editor = self.editor

        if root is None:
            root = factory()

        create_path = root.path.create
        update_data = editor.update

        if path_name is None:
            if hasattr(rows, "itertuples"):
                rows = rows.itertuples(index=False)
            for row in rows:
                if isinstance(row, str):
                    row = row.split(sep)
                create_path(row)
        elif isinstance(path_name, str):
            if hasattr(rows, "to_dict"):
                rows = rows.to_dict('records')
            for row in rows:
                data = {k: v for (k, v) in row.items() if k != path_name}
                path = row[path_name]
                if isinstance(path, str):
                    path = path.split(sep)
                node = create_path(path)
                update_data(node, data)
        else:
            if hasattr(rows, "to_dict"):
                rows = rows.to_dict('records')
            for row in rows:
                path_iter = (row.get(segment) for segment in path_name)
                path = tuple(itertools.takewhile(lambda s: s is not None, path_iter))
                data = {k: v for (k, v) in row.items() if k not in path_name}
                node = create_path(path)
                update_data(node, data)
        return root

    def to_rows(self, tree: TNode, with_root: bool = False, leaves_only: bool = False):
        path_name = self.path_name
        sep = self.sep
        editor = self.editor

        if path_name is None:
            for path, _ in self._iter_paths(tree, with_root, leaves_only):
                yield tuple(path)
        elif isinstance(path_name, str):
            for path, node in self._iter_paths(tree, with_root, leaves_only):
                data = editor.get_attributes(node)
                data[path_name] = sep.join(path) if sep is not None else tuple(path)
                yield data
        else:
            for path, node in self._iter_paths(tree, with_root, leaves_only):
                if len(path) > len(path_name):
                    msg = f"Path {tuple(path)} doesn't fit in {path_name}"
                    raise RowSerializerError(msg)
                data = {name: segment for (name, segment) in zip(path_name, path)}
                data.update(editor.get_attributes(node))
                yield data

    @staticmethod
    def _iter_paths(root: TNode, with_root: bool, leaves_only: bool):
        row = []
        if with_root:
            row.append(root.identifier)
            yield row, root
        for node, item in root.descendants.preorder():
            row = row[:item.depth + with_root - 1]
            row.append(node.identifier)
            if not leaves_only or node.is_leaf:
                yield row, node


class RowSerializerError(Exception):
    pass
