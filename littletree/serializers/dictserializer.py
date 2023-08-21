from typing import Mapping, TypeVar, Type
from ..basenode import BaseNode

TNode = TypeVar("NodeType", bound=BaseNode)


class DictSerializer:
    def __init__(self, factory: Type[TNode], identifier=None, children="children", fields=()):
        """
        Read / write tree from nested dictonary

        :param identifier: How to find identifier in dict. If none, assume key-value pairs.
        :param children: How to find children in dict. If none, use complete dict.
        :param fields: Which fields from data to pass to constructor as named arguments.
        :param factory: Factory method for Node construction
        """

        self.factory = factory
        self.identifier = identifier
        self.children = children
        self.fields = fields

    def from_dict(self, data: Mapping) -> TNode:
        """
        Load tree from data

        :param data: Dictionary in which tree is stored
        :return: Root node of new tree
        """
        identifier = self.identifier
        fields = self.fields
        children = self.children

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

        identifier = self.identifier
        children = self.children
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
            data.update({field: getattr(node, field) for field in fields})

            if child_data:
                data[children] = child_data
        else:
            data = child_data

        return data
