from collections.abc import MutableMapping, MutableSequence
from typing import Optional

from littletree import Node
from littletree.exceptions import DuplicateChildError

class IndexedTreeDict(MutableMapping):
    def __init__(self):
        self._mapping = {}
        self._seq = []

    def pop(self, key, /):
        removed_node = self._mapping[key]
        self._seq.pop(removed_node.index)
        del self._mapping[key]
        return removed_node

    def __getitem__(self, key, /):
        return self._mapping[key]

    def __setitem__(self, key, node, /):
        if replaced_node := self._mapping.get(key):
            index = replaced_node.index
            self._seq[index] = node
        else:
            index = len(self._seq)
            self._seq.append(node)

        node._index = index
        self._mapping[key] = node

    __delitem__ = pop

    def __len__(self):
        return len(self._seq)

    def __iter__(self):
        return (node.identifier for node in self._seq)

    def clear(self):
        self._seq.clear()
        self._mapping.clear()

    def reverse(self):
        return self._seq.reverse()

    def sort(self, key=None, reverse=False):
        self._seq.sort(key=key, reverse=reverse)


class IndexedTreeChildren(MutableSequence):
    def __init__(self, dict: IndexedTreeDict, parent):
        self._parent = parent
        self._mapping = dict._mapping
        self._seq = dict._seq

    def insert(self, index, node: Node, check_loop=True):
        if index < 0:
            index += len(self._seq)
        if node.identifier in self._mapping:
            raise DuplicateChildError
        self._seq.insert(index, node)
        self._mapping[node.identifier] = node
        node._index = index
        node._parent = self._parent

    def pop(self, index=-1):
        node = self._seq.pop(index)
        del self._mapping[node.identifier]
        node._parent = None
        return node

    def __getitem__(self, index: int | slice):
        return self._seq[index]

    def __setitem__(self, index, node):
        if index < 0:
            index += len(self._seq)
        replaced_node = self._seq[index]
        if (node.identifier in self._mapping
                and node.identifier != replaced_node.identifier):
            raise DuplicateChildError
        self._seq[index] = node
        del self._mapping[replaced_node.identifier]
        self._mapping[node.identifier] = node
        replaced_node._parent = None
        node._parent = self._parent

    __delitem__ = pop

    def __len__(self):
        return len(self._seq)


class IndexedNode(Node):
    """This is like node, but the children can be accessed and stored by index."""
    __slots__ = "_index"
    dict_class = IndexedTreeDict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self._parent is not None:
            self._index = len(self._parent._cdict)
        else:
            self._index = None

    @property
    def children(self) -> IndexedTreeChildren:
        try:
            return self._cvalues
        except AttributeError:
            cvalues = IndexedTreeChildren(self._cdict, self)
            self._cvalues = cvalues
            return cvalues

    @property
    def index(self) -> Optional[int]:
        """This returns the index of this node relative to its siblings.

        If the node is the root, this returns None.
        """
        # Child is root
        if self._parent is None:
            return None

        _index = self._index
        _keys = self._parent._cdict._seq

        # Best case scenario is constant time
        if _keys[_index] is self:
            return _index

        # Worst-case scenario is linear time
        index = _keys.index(self, _index - 15, _index + 15)
        if index == -1:
            index = _keys.index(self, 0, _index - 15)
            if index == -1:
                index = _keys.index(self, _index + 15)

            assert index != -1

        self._index = index
        return index


def main():
    tree = IndexedNode()
    tree.children.append(IndexedNode("where"))
    tree.children.append(IndexedNode("love"))
    tree.children.insert(1, IndexedNode("is"))
    tree.children.insert(2, IndexedNode("the"))
    tree.show("{0.index} has {0.data}")

main()
