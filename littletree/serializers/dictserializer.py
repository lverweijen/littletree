from typing import Mapping, TypeVar, Type, Hashable, Optional
from ..basenode import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)
TIdentifier = TypeVar("TIdentifier", bound=Hashable)


class DictSerializer:
    __slots__ = "factory", "node_name", "children_name", "fields"

    def __init__(
        self,
        factory: Type[TNode] = None,
        node_name: TIdentifier = None,
        children_name: Optional[str] = "children",
        fields=(),
    ):
        """
        Read / write tree from nested dictionary

        :param node_name: How to find identifier in dict. If none, assume key-value pairs.
        :param children_name: How to find children in dict. If none, use complete dict.
        :param fields: Which fields from data to pass to constructor as named arguments.
        :param factory: Factory method for Node construction
        """
        if factory is None:
            from ..node import Node
            factory = Node

        if not isinstance(fields, str):
            if node_name in fields:
                raise ValueError(f"fields can not contain node_name")
            if children_name in fields:
                raise ValueError(f"fields can not contain children_name")

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
        if self.node_name:
            from_func = self._from_cvalues  # Children stored as list
        else:
            from_func = self._from_cdict  # Children stored as dict (root is nameless)

        if isinstance(self.fields, str):
            set_data = self._set_node_data  # One field is a mapping
        else:
            set_data = self._set_node_fields  # Multiple fields are synchronized

        return from_func(data, set_data=set_data)

    def _from_cvalues(self, data: Mapping, set_data) -> TNode:
        # Node name is stored as a field
        factory = self.factory
        node_name = self.node_name
        children_name = self.children_name

        stack = []
        tree = parent = factory()
        tree.identifier = data[node_name]
        set_data(tree, data)
        children = iter(data[children_name])
        while (data_node := next(children, None)) or stack:
            if data_node:
                node = factory()
                set_data(node, data_node)
                parent[data_node[node_name]] = node
                if node_children := data_node.get(children_name):
                    stack.append((parent, children))
                    parent, children = node, iter(node_children)
            else:
                parent, children = stack.pop()
        return tree

    def _from_cdict(self, data: Mapping, set_data) -> TNode:
        # Node name is stored as a key. This means the root is nameless
        factory = self.factory
        children_name = self.children_name

        tree = parent = factory()
        set_data(tree, data)
        children = dict(data[self.children_name]) if children_name else dict(data)
        stack = []
        while children or stack:
            if children:
                node = self.factory()
                name, data_node = children.popitem()
                parent[name] = node
                set_data(node, data_node)
                if node_children := data_node.get(children_name) if children_name else data_node:
                    stack.append((parent, children))
                    parent, children = node, node_children
            else:
                parent, children = stack.pop()
        return tree

    def to_dict(self, tree: TNode) -> Mapping:
        """
        Convert Node to a dictionary.

        :param tree: Node to convert
        :return: Nested dictionary of node and children
        """
        node_name = self.node_name
        if node_name:
            to_func = self._to_cvalues
        else:
            to_func = self._to_cdict

        if isinstance(self.fields, str):
            get_data = self._get_node_data
        else:
            get_data = self._get_node_fields

        return to_func(tree, get_data=get_data)

    def _to_cvalues(self, tree: TNode, get_data) -> Mapping:
        children_name = self.children_name

        last_mapping = {self.node_name: tree.identifier}
        last_mapping.update(get_data(tree))
        stack = [last_mapping]
        for node, item in tree.iter_descendants(order="pre", with_item=True):
            if item.depth > len(stack):
                stack.append(last_mapping)
            else:
                while item.depth < len(stack):
                    stack.pop()
            last_mapping = {self.node_name: node.identifier}
            last_mapping.update(get_data(node))

            parent = stack[-1]
            if children_name not in parent:
                parent[children_name] = []
            parent[children_name].append(last_mapping)

        return stack[0]

    def _to_cdict(self, tree: TNode, get_data) -> Mapping:
        children_name = self.children_name

        last_mapping = dict(get_data(tree))
        stack = [last_mapping]
        for node, item in tree.iter_descendants(order="pre", with_item=True):
            if item.depth > len(stack):
                stack.append(last_mapping)
            else:
                while item.depth < len(stack):
                    stack.pop()
            last_mapping = dict(get_data(node))
            parent = stack[-1]
            if children_name:
                if children_name not in parent:
                    parent[children_name] = {}
                parent[children_name][node.identifier] = last_mapping
            else:
                parent[node.identifier] = last_mapping

        return stack[0]

    def _get_node_data(self, node):
        return getattr(node, self.fields)

    def _get_node_fields(self, node):
        return {field: getattr(node, field) for field in self.fields}

    def _set_node_data(self, node, data):
        data = {k: v for (k, v) in data.items() if k not in [self.node_name, self.children_name]}
        setattr(node, self.fields, data)

    def _set_node_fields(self, node, data):
        fields = self.fields
        for field, value in data.items():
            if field in fields:
                setattr(node, field, value)
