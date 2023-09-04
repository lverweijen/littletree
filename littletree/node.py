import copy
from typing import Mapping, Optional, Iterator, TypeVar, Generic, Hashable, Union, Iterable

from .basenode import BaseNode
from .exporters import DotExporter
from .exporters import StringExporter
from .serializers import DictSerializer
from .serializers import RelationSerializer
from .serializers import RowSerializer
from .serializers import NewickSerializer

TNode = TypeVar("TNode", bound="Node")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)
TData = TypeVar("TData")

MISSING = object()


class Node(BaseNode[TIdentifier], Generic[TIdentifier, TData]):
    __slots__ = "data"

    def __init__(
        self,
        data: TData = MISSING,
        identifier: TIdentifier = "node",
        children: Union[Mapping[TIdentifier, TNode], Iterable[TNode]] = (),
        parent: Optional[TNode] = None,
    ):
        """
        Create a Node

        :param identifier: Identifier for this node
        :param parent: Immediately assign a parent
        :param children: Children to add
        """
        super().__init__(identifier, children, parent)
        if data is MISSING:
            data = {}
        self.data = data

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
        return ((self.identifier, self.data, self._cdict)
                == (other.identifier, other.data, other._cdict))

    def _bare_copy(self):
        return self.__class__(data=self.data)

    def _bare_deepcopy(self, memo=None):
        return self.__class__(data=copy.deepcopy(self.data, memo))

    def to_string(self, file=None, keep=None, str_factory=None, **kwargs) -> Optional[str]:
        exporter = StringExporter(str_factory=str_factory, **kwargs)
        return exporter.to_string(self, file, keep=keep)

    def to_image(self, file=None, keep=None, node_attributes=None, **kwargs):
        if node_attributes is None:
            node_attributes = {"label": str}
        exporter = DotExporter(node_attributes=node_attributes, **kwargs)
        return exporter.to_image(self, file, keep=keep)

    def to_dot(self, file=None, keep=None, node_attributes=None, **kwargs) -> Optional[str]:
        if node_attributes is None:
            node_attributes = {"label": str}
        exporter = DotExporter(node_attributes=node_attributes, **kwargs)
        return exporter.to_dot(self, file, keep=keep)

    @classmethod
    def from_dict(cls, data, fields="data", **kwargs) -> TNode:
        """
        Load tree from Dict.
        :param fields: Fields to export
        :param data: Dict in which tree is stored
        :return: Root node of new tree
        """
        return DictSerializer(cls, fields=fields, **kwargs).from_dict(data)

    def to_dict(self, fields="data", **kwargs) -> Mapping:
        return DictSerializer(self.__class__, fields=fields, **kwargs).to_dict(self)

    @classmethod
    def from_rows(cls, rows, root=None, fields="data", **kwargs) -> TNode:
        return RowSerializer(cls, fields=fields, **kwargs).from_rows(rows, root)

    def to_rows(self, fields="data", **kwargs) -> Iterator[Mapping]:
        return RowSerializer(self.__class__, fields=fields, **kwargs).to_rows(self)

    @classmethod
    def from_relations(cls, relations, root=None, fields="data", **kwargs) -> TNode:
        serializer = RelationSerializer(cls, fields=fields, **kwargs)
        return serializer.from_relations(relations, root)

    def to_relations(self, fields="data", **kwargs):
        return RelationSerializer(self.__class__, fields=fields, **kwargs).to_relations(self)

    @classmethod
    def from_newick(cls, file=None, text=None, root=None, fields="data", **kwargs) -> TNode:
        serializer = NewickSerializer(cls, fields=fields, **kwargs)
        if text:
            return serializer.loads(text, root)
        else:
            return serializer.load(file, root)

    def to_newick(self, file=None, fields="data", **kwargs) -> Optional[str]:
        serializer = NewickSerializer(self.__class__, fields=fields, **kwargs)
        if file:
            return serializer.dump(self, file)
        else:
            return serializer.dumps(self)
