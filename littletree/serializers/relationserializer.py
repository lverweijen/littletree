from typing import Callable, Sequence, Mapping, TypeVar

from littletree import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)


class RelationSerializer:
    """Serializes a tree to a list of parent-children relations."""

    def __init__(
        self,
        factory: Callable[[], TNode] = None,
        child_name="identifier",
        parent_name="parent",
        fields=(),
    ):
        """
        Create path serializer. Useful to convert to/from csv-like formats.
        :param factory: How to create a node
        :param child_name: Column containing child name
        :param parent_name: Column containing parent name
        :param fields: Fields to include. If fields is a string, include as dictionary.
        If fields is sequence, add each attribute.
        """
        if factory is None:
            from ..node import Node
            factory = Node

        self.factory = factory
        self.child_name = child_name
        self.parent_name = parent_name
        self.fields = fields

    def from_relations(self, rows: Sequence[Mapping], root=None):
        factory = self.factory
        child_name, parent_name, fields = self.child_name, self.parent_name, self.fields

        nodes = {}

        # Special case for pandas data frame (and similar apis)
        if hasattr(rows, "to_dict"):
            rows = rows.to_dict("records")

        if root is None:
            root = factory()
        for row in rows:
            child_id = row[child_name]
            child = nodes.get(child_id)
            if child is None:
                child = nodes[child_id] = factory()
                child.identifier = child_id

            parent_id = row[parent_name]
            parent = nodes.get(parent_id)
            if parent is None:
                parent = nodes[parent_id] = factory()
                parent.identifier = parent_id
            child.parent = parent

            if fields:
                if isinstance(fields, str):
                    data = {}
                    for field, value in row.items():
                        if field not in (child_name, parent_name):
                            data[field] = value
                    child.data = data
                else:
                    for field in fields:
                        setattr(child, field, row[field])

        if not isinstance(root, BaseNode):
            root = nodes[root]

        for node in nodes.values():
            if node.is_root and node is not root:
                node.parent = root

        return root

    def to_relations(self, root: TNode):
        child_name, parent_name, fields = self.child_name, self.parent_name, self.fields
        for node in root.iter_descendants():
            relation = {child_name: node.identifier, parent_name: node.parent.identifier}
            if fields:
                if isinstance(fields, str):
                    data = getattr(node, fields)
                    if data:
                        relation.update(data)
                else:
                    relation.update({field: getattr(node, field) for field in fields})
            yield relation
