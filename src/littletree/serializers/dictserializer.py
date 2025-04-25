from typing import Mapping, TypeVar, Type, Hashable, Optional, Sequence

from ._nodeeditor import get_editor
from ..basenode import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)
TIdentifier = TypeVar("TIdentifier", bound=Hashable)


class DictSerializer:
    __slots__ = "factory", "node_name", "children_name", "editor"

    def __init__(
        self,
        factory: Type[TNode] = None,
        identifier_name: TIdentifier = "identifier",
        children_name: Optional[str] = "children",
        fields: Sequence[str] = (),
        data_field: str = None,
    ):
        """
        Read / write tree from nested dictionary

        :param identifier_name: How to find identifier in dict. If none, assume key-value pairs.
        :param children_name: How to find children in dict. If none, use complete dict.
        :param fields: Which fields from data to pass to constructor as named arguments.
        :param factory: Factory method for Node construction
        """
        if factory is None:
            from ..node import Node
            factory = Node

        if not isinstance(fields, str):
            if identifier_name in fields:
                raise ValueError(f"fields can not contain node_name")
            if children_name in fields:
                raise ValueError(f"fields can not contain children_name")

        self.factory = factory
        self.node_name = identifier_name
        self.children_name = children_name
        self.editor = get_editor(fields, data_field)

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

        return from_func(data, self.editor.update)

    def _from_cvalues(self, data: Mapping, set_data) -> TNode:
        # Node name is stored as a field
        factory = self.factory
        node_name = self.node_name
        children_name = self.children_name

        data = data.copy()
        stack = []
        tree = parent = factory()
        tree.identifier = data[node_name]
        children = iter(data[children_name])
        data = {k: v for (k, v) in data.items() if k not in [node_name, children_name]}
        set_data(tree, data)
        while (data_node := next(children, None)) or stack:
            if data_node:
                node = factory()
                parent[data_node.pop(node_name)] = node
                if node_children := data_node.get(children_name):
                    stack.append(children)
                    parent, children = node, iter(node_children)
                data = {k: v for (k, v) in data_node.items() if k not in [node_name, children_name]}
                set_data(node, data)
            else:
                parent, children = parent.parent, stack.pop()
        return tree

    def _from_cdict(self, data: Mapping, set_data) -> TNode:
        # Node name is stored as a key. This means the root is nameless
        factory = self.factory
        children_name = self.children_name

        tree = parent = factory()

        if children_name:
            data = dict(data)
            children = data.pop(self.children_name, None)
            set_data(tree, data)
        else:
            children = data
        stack = []
        while children or stack:
            if children:
                node = self.factory()
                name, data_node = children.popitem()
                parent[name] = node
                if node_children := data_node.get(children_name) if children_name else data_node:
                    stack.append(children)
                    parent, children = node, node_children
                data = {k: v for (k, v) in data_node.items() if k != children_name}
                set_data(node, data)
            else:
                parent = parent.parent
                children = stack.pop()
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

        return to_func(tree, get_data=self.editor.get_attributes)

    def _to_cvalues(self, tree: TNode, get_data) -> Mapping:
        children_name = self.children_name

        last_mapping = {self.node_name: tree.identifier}
        last_mapping.update(get_data(tree))
        stack = [last_mapping]
        for node, item in tree.descendants.preorder():
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
        for node, item in tree.descendants.preorder():
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
