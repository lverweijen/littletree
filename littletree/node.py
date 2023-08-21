import copy
from typing import Mapping, Optional, Iterator, TypeVar, Generic, Hashable, Union, Iterable

from .basenode import BaseNode
from .exporters.dotexporter import DotExporter
from .exporters.stringexporter import StringExporter
from .serializers.dictserializer import DictSerializer
from .serializers.rowserializer import RowSerializer

TNode = TypeVar("TNode", bound="Node")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)
TData = TypeVar("TData")


class Node(BaseNode[TIdentifier], Generic[TIdentifier, TData]):
    __slots__ = "data"

    def __init__(
        self,
        data: TData = None,
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
        self.data = data

    def __repr__(self) -> str:
        output = [self.__class__.__name__, f"({self.data!r}, identifier={self.identifier!r})"]
        return "".join(output)

    def __eq__(self: TNode, other: TNode):
        if self is other:
            return True
        return ((self.identifier, self.data, self._cdict)
                == (other.identifier, other.data, other._cdict))

    def __copy__(self):
        return self.__class__(self.data,
                              identifier=self.identifier,
                              children={k: v.__copy__() for (k, v) in self._cdict.items()})

    def __deepcopy__(self, memo):
        return self.__class__(copy.deepcopy(self.data, memo),
                              identifier=self.identifier,
                              children={k: v.__deepcopy__(memo) for (k, v) in self._cdict.items()})

    copy = __copy__

    @classmethod
    def from_dict(cls, data, **kwargs) -> TNode:
        """
        Load tree from dictionary
        :param data: Dictionary in which tree is stored
        :return: Root node of new tree
        """
        return DictSerializer(cls, fields=["data"], **kwargs).from_dict(data)

    @classmethod
    def from_paths(cls, rows, **kwargs) -> TNode:
        return RowSerializer(cls, fields=["data"], **kwargs).from_rows(rows)

    def to_string(self, file=None, keep=None, **kwargs) -> Optional[str]:
        def str_factory(node):
            if node.data is not None:
                return f"{node.identifier}: {node.data}"
            else:
                return f"{node.identifier}"

        exporter = StringExporter(str_factory=str_factory, **kwargs)
        return exporter.to_string(self, file, keep=keep)

    def to_image(self, file=None, keep=None, **kwargs):
        exporter = DotExporter(node_attributes={"label": Node._graphviz_label}, **kwargs)
        return exporter.to_image(self, file, keep=keep)

    def to_dot(self, file=None, keep=None, **kwargs) -> Optional[str]:
        exporter = DotExporter(node_attributes={"label": Node._graphviz_label}, **kwargs)
        return exporter.to_dot(self, file, keep=keep)

    def to_dict(self, **kwargs) -> Mapping:
        return DictSerializer(self.__class__, fields=["data"], **kwargs).to_dict(self)

    def to_rows(self, **kwargs) -> Iterator[Mapping]:
        return RowSerializer(self.__class__, fields=["data"], **kwargs).to_rows(self)

    def _graphviz_label(self):
        if self.data is None:
            return f"{self.identifier}"
        else:
            return f"{self.identifier}\n{self.data}"
