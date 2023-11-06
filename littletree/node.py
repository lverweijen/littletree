import copy
import sys
from typing import Mapping, Optional, Iterator, TypeVar, Generic, Hashable, Union, Iterable

from .basenode import BaseNode
from .exporters import DotExporter
from .exporters import MermaidExporter
from .exporters import StringExporter
from .serializers import DictSerializer
from .serializers import NewickSerializer
from .serializers import RelationSerializer
from .serializers import RowSerializer

TNode = TypeVar("TNode", bound="Node")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)
TData = TypeVar("TData")

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

    def __eq__(self: TNode, other: TNode):
        if self is other:
            return True
        elif isinstance(other, Node):
            return ((self.identifier, self.data, self._cdict)
                    == (other.identifier, other.data, other._cdict))
        else:
            return NotImplemented

    def show(self, style=None, **kwargs):
        """Print this tree. Shortcut for print(tree.to_string())."""
        if sys.stdout:
            if not style:
                supports_unicode = not sys.stdout.encoding or sys.stdout.encoding.startswith('utf')
                style = "square" if supports_unicode else "ascii"
            self.to_string(sys.stdout, style=style, **kwargs)

    def copy(self, memo=None) -> TNode:
        """Make a shallow copy or deepcopy if memo is passed."""
        if memo:
            def node(original, _):
                return Node(copy.deepcopy(original.data, memo))
        else:
            def node(original, _):
                return Node(original.data)
        return self.transform(node)

    def compare(self, other: TNode, keep_equal=False) -> Optional[TNode]:
        """Compare two trees to one another.

        If diff_only is true, all nodes where data is equal will be removed.

        >>> tree = Node('apples', identifier='fruit')
        >>> other_tree = Node('oranges')
        >>> tree.compare(other_tree)
        Node({'self': 'apples', 'other': 'oranges'}, identifier='fruit)
        """
        diff_node = self.transform(lambda _, _i: Node({'self': self.data}))
        diff_node.data['other'] = other.data
        insert_depth = 0
        for node, item in other.iter_descendants(with_item=True):
            while insert_depth >= item.depth:
                insert_depth -= 1
                diff_node = diff_node.parent
            diff_node = diff_node.path.create([node.identifier])
            diff_node.data['other'] = node.data
            insert_depth += 1
        diff_tree = diff_node.root
        if not keep_equal:
            to_detach = None
            for node in diff_tree.iter_tree(order='post'):
                if to_detach:
                    to_detach.detach()
                if node.data.get('self') == node.data.get('other'):
                    if node.is_leaf:
                        to_detach = node  # Should be detached next round, because of up-traversal
                    else:
                        node.data.clear()
            if diff_tree is to_detach:
                return None  # Trees are perfectly equal
        return diff_tree

    def to_string(self, file=None, keep=None, str_factory=None, **kwargs) -> Optional[str]:
        exporter = StringExporter(str_factory=str_factory, **kwargs)
        return exporter.to_string(self, file, keep=keep)

    def to_image(
        self,
        file=None,
        keep=None,
        node_attributes=None,
        node_label=str,
        backend="graphviz",
        **kwargs
    ):
        if node_attributes is None:
            node_attributes = {"label": node_label}
        if backend == "graphviz":
            exporter = DotExporter(node_attributes=node_attributes, **kwargs)
        elif backend == "mermaid":
            exporter = MermaidExporter(node_label=node_label, **kwargs)
            if not file:
                raise ValueError("Parameter file is required for mermaid")
        else:
            raise ValueError(f"Backend should be graphviz or mermaid, not {backend}")
        return exporter.to_image(self, file, keep=keep)

    def to_dot(self, file=None, keep=None, node_attributes=None, node_label=str, **kwargs) -> Optional[str]:
        if node_attributes is None:
            node_attributes = {"label": node_label}
        exporter = DotExporter(node_attributes=node_attributes, **kwargs)
        return exporter.to_dot(self, file, keep=keep)

    def to_mermaid(self, file=None, keep=None, node_label=str, **kwargs) -> Optional[str]:
        exporter = MermaidExporter(node_label=node_label, **kwargs)
        return exporter.to_mermaid(self, file, keep=keep)

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
