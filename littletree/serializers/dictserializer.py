from typing import Mapping, TypeVar, Type, Hashable, Optional
from ..basenode import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)
TIdentifier = TypeVar("TIdentifier", bound=Hashable)


class DictSerializer:
    def __init__(
        self,
        factory: Type[TNode] = None,
        node_name: TIdentifier = None,
        children_name: Optional[str] = "children",
        fields=(),
    ):
        """
        Read / write tree from nested dictonary

        :param node_name: How to find identifier in dict. If none, assume key-value pairs.
        :param children_name: How to find children in dict. If none, use complete dict.
        :param fields: Which fields from data to pass to constructor as named arguments.
        :param factory: Factory method for Node construction
        """
        if factory is None:
            from ..node import Node
            factory = Node

        self.factory = factory
        self.node_name = node_name
        self.children_name = children_name
        self.fields = fields

    def from_dict(self, data: Mapping) -> TNode:
        """
        Load tree from data

        :param data: Dictionary in which tree is stored
        :return: Root node of new tree
        """
        identifier = self.node_name
        fields = self.fields
        children = self.children_name

        if isinstance(fields, str):
            field_data = {k: v for (k, v) in getattr(data, fields).items()
                          if k not in (identifier, children)}
        else:
            field_data = {k: v for (k, v) in data.items() if k in fields}

        node = self.factory(**field_data)

        if identifier is not None and identifier not in fields:
            node.identifier = data[identifier]

        child_data = data if children is None else data.get(children, ())
        if isinstance(child_data, Mapping):
            child_data = {k: self.from_dict(v) for (k, v) in child_data.items()}
        else:
            child_data = [self.from_dict(v) for v in child_data]

        node.update(child_data)
        return node

    def to_dict(self, node: TNode) -> Mapping:
        """
        Convert Node to a dictionary.

        :param node: Node to convert
        :return: Nested dictionary of node and children
        """

        identifier = self.node_name
        children = self.children_name
        fields = self.fields

        if identifier is None:
            data = {}
            child_data = {child.identifier: self.to_dict(child) for child in node.children}
        else:
            data = {identifier: node.identifier}
            child_data = [self.to_dict(child) for child in node.children]

        if not children and (identifier or fields):
            raise ValueError("If children is None, identifier and fields should also be None")
        elif children is not None:
            if isinstance(fields, str):
                mapping = getattr(node, fields)
                try:
                    data.update(mapping)
                except ValueError as e:
                    msg = (f"{fields} might not be a dictionary. "
                           f"Consider node.to_dict(fields=['{fields}']) instead.")
                    raise ValueError(msg) from e
            else:
                data.update({field: getattr(node, field) for field in fields})

            if child_data:
                data[children] = child_data
        else:
            data = child_data

        return data
