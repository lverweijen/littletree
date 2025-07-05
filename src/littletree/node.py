import copy
from typing import Mapping, Optional, Iterator, TypeVar, Generic, Hashable, Union, Iterable

from .basenode import BaseNode
from .serializers import DictSerializer
from .serializers import NetworkXSerializer
from .serializers import NewickSerializer
from .serializers import RelationSerializer
from .serializers import RowSerializer

TNode = TypeVar("TNode", bound="Node")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)
TData = TypeVar("TData")
TInput = TypeVar("TInput")

MISSING = object()


class Node(BaseNode[TIdentifier], Generic[TIdentifier, TData]):
    __slots__ = "data"

    def __init__(
        self,
        data: TData = MISSING,
        identifier: TIdentifier = MISSING,
        children: Union[Mapping[TIdentifier, TNode], Iterable[TNode]] = (),
        parent: Optional[TNode] = None,
    ):
        """
        Create a Node

        :param identifier: Identifier for this node
        :param parent: Immediately assign a parent
        :param children: Children to add
        """
        identifier = id(self) if identifier is MISSING else identifier
        super().__init__(identifier, children, parent)
        self.data = {} if data is MISSING else data

    def __repr__(self) -> str:
        output = [self.__class__.__name__, f"({self.data!r}, identifier={self.identifier!r})"]
        return "".join(output)

    def __str__(self):
        if not self.data:
            return f"{self.identifier}"
        else:
            return f"{self.identifier}\n{self.data}"

    def similar_to(self: TNode, other: TNode):
        """Check if two trees are similar.

        Trees are similar if they have the same structure and the same data.

        Change from version 0.5.0:
        - Two trees can now be equal if the roots have a different identifier.
        """
        if self is other:
            return True
        elif isinstance(other, self.__class__):
            return all(n1.data == n2.data and n1._cdict.keys() == n2._cdict.keys()
                       for n1, n2 in self.iter_together(other))
        else:
            return NotImplemented

    def copy(self, memo=None, *, keep=None, deep=False) -> TNode:
        """Make a shallow copy or deepcopy if memo is passed."""
        if deep or memo:
            def node(original):
                return Node(identifier=original.identifier,
                            data=copy.deepcopy(original.data, memo or {}))
        else:
            def node(original):
                return Node(identifier=original.identifier, data=original.data)
        return self.transform(node, keep=keep)

    def compare(self, other: TNode, keep_equal=False) -> Optional[TNode]:
        """Compare two trees to one another.

        If keep_equal is False (default), all nodes where data is equal will be removed.

        >>> tree = Node('apples', identifier='fruit')
        >>> other_tree = Node('oranges')
        >>> tree.compare(other_tree)
        Node({'self': 'apples', 'other': 'oranges'}, identifier='fruit)
        """
        diff_node = self.transform(lambda n: Node(identifier=n.identifier, data={'self': n.data}))
        diff_node.data['other'] = other.data
        insert_depth = 0
        for node, item in other.descendants.preorder():
            while insert_depth >= item.depth:
                insert_depth -= 1
                diff_node = diff_node.parent
            diff_node = diff_node.path.create([node.identifier])
            diff_node.data['other'] = node.data
            insert_depth += 1
        diff_tree = diff_node.root
        if not keep_equal:
            for node, _ in diff_tree.nodes.postorder():
                if node.data.get('self') == node.data.get('other'):
                    if node.is_leaf:
                        node.detach()
                    else:
                        node.data.clear()
            if diff_tree.is_leaf and diff_tree.data.get('self') == diff_tree.data.get('other'):
                return None  # Trees are perfectly equal
        return diff_tree

    @classmethod
    def from_dict(cls, data, data_field="data", **kwargs) -> TNode:
        return DictSerializer(cls, data_field=data_field, **kwargs).from_dict(data)

    def to_dict(self, data_field="data", **kwargs) -> Mapping:
        return DictSerializer(self.__class__, data_field=data_field, **kwargs).to_dict(self)

    @classmethod
    def from_rows(cls, rows, root=None, data_field="data", **kwargs) -> TNode:
        return RowSerializer(cls, data_field=data_field, **kwargs).from_rows(rows, root)

    def to_rows(self, data_field="data", **kwargs) -> Iterator[Mapping]:
        return RowSerializer(self.__class__, data_field=data_field, **kwargs).to_rows(self)

    @classmethod
    def from_relations(cls, relations, root=None, data_field="data", **kwargs) -> TNode:
        serializer = RelationSerializer(cls, data_field=data_field, **kwargs)
        return serializer.from_relations(relations, root)

    def to_relations(self, data_field="data", **kwargs):
        serializer = RelationSerializer(self.__class__, data_field=data_field, **kwargs)
        return serializer.to_relations(self)

    @classmethod
    def from_newick(cls, newick, root=None, data_field="data", **kwargs) -> TNode:
        serializer = NewickSerializer(cls, data_field=data_field, **kwargs)
        if isinstance(newick, (str, bytes, bytearray)):
            return serializer.loads(newick, root)
        else:
            return serializer.load(newick, root)

    def to_newick(self, file=None, data_field="data", **kwargs) -> Optional[str]:
        serializer = NewickSerializer(self.__class__, data_field=data_field, **kwargs)
        if file:
            return serializer.dump(self, file)
        else:
            return serializer.dumps(self)

    @classmethod
    def from_networkx(cls, graph, **kwargs):
        exporter = NetworkXSerializer(cls, data_field="data", **kwargs)
        return exporter.from_networkx(graph)

    def to_networkx(self, **kwargs):
        exporter = NetworkXSerializer(self.__class__, data_field="data", **kwargs)
        return exporter.to_networkx(self)
