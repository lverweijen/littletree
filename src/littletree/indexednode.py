from collections.abc import MutableMapping, MutableSequence
from typing import Optional

from littletree import Node
from littletree.exceptions import DuplicateChildError, TreeException


class IndexedTreeDict(MutableMapping):
    __slots__ = "_mapping", "_seq"

    # This class is private and may ignore parents of nodes.
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


class IndexedTreeChildren(MutableSequence):
    __slots__ = "_parent", "_mapping", "_seq"

    # The interface is public and all methods should leave the tree into a valid state.
    def __init__(self, dict: IndexedTreeDict, parent):
        self._parent = parent
        self._mapping = dict._mapping
        self._seq = dict._seq

    def __repr__(self):
        return f"<{type(self).__qualname__} {self._seq}>"

    def insert(self, index, node: Node, check_loop=True):
        """Add node to children at index."""
        if index < 0:
            index += len(self._seq)
        if node.identifier in self._mapping:
            raise DuplicateChildError
        self._seq.insert(index, node)
        self._mapping[node.identifier] = node
        node._index = index
        node._parent = self._parent

    def pop(self, index=-1):
        """Remove and return node from chidren at index."""
        node = self._seq.pop(index)
        del self._mapping[node.identifier]
        node._parent = None
        return node

    def reverse(self):
        """Reverses order of children."""
        self._seq.reverse()
        for i, n in enumerate(self._seq):
            n._index = i

    def sort(self, key=None, reverse=False):
        """Sorts children."""
        self._seq.sort(key=key, reverse=reverse)
        for i, n in enumerate(self._seq):
            n._index = i

    def swap(self, i, j):
        """Swap two children."""
        _seq = self._seq
        _seq[i], _seq[j] = _seq[j], _seq[i]
        _seq[i]._index = i
        _seq[j]._index = j

    def __getitem__(self, index: int | slice):
        return self._seq[index]

    def __setitem__(self, index, node):
        match index:
            case int():
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
                node._index = index
            case slice(start, stop, step):
                n_len = len(self._seq)
                if start < 0: start += n_len
                if stop < 0: stop += n_len

                new_nodes = node

                # Check for doubles within new nodes
                new_identifiers = {n.identifier for n in new_nodes}
                if len(new_identifiers) < len(node):
                    raise DuplicateChildError

                # Check that new nodes don't already exist
                old_nodes = self[index]
                old_identifiers = {n.identifier for n in old_nodes}
                if (new_identifiers - old_identifiers) & self._mapping.keys():
                    raise DuplicateChildError

                # Actually perform the update
                self._seq[index] = node
                for n in old_nodes:
                    n._parent = None
                    del self._mapping[n.identifier]
                for i, n in zip(range(start, stop, step or 1), new_nodes):
                    n._index = i
                    n._parent = self._parent
                    self._mapping[n.identifier] = n
            case _:
                raise TypeError

    def __delitem__(self, index):
        match index:
            case int():
                self.pop(index)
            case slice():
                del self._seq[index]
                old_nodes = self[index]
                for n in old_nodes:
                    n._parent = None
                    del self._mapping[n.identifier]
            case _:
                raise TypeError

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

    @property
    def children(self) -> IndexedTreeChildren:
        """Get children, but provide a richer interface than a normal Node."""
        try:
            return self._cvalues
        except AttributeError:
            cvalues = IndexedTreeChildren(self._cdict, self)
            self._cvalues = cvalues
            return cvalues

    @property
    def index(self) -> Optional[int]:
        """This returns the index of this node relative to its siblings.

        If this node is the root, None is returned.
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

    @index.setter
    def index(self, new_index: int):
        """Changing the index is done by swapping the positions of the nodes."""
        if parent := self._parent:
            parent.children.swap(self.index, new_index)
        else:
            raise TreeException("Can't change index of root.")


from abstracttree import generics
generics.children.register(IndexedNode, IndexedNode.children.fget)


def main():
    tree = IndexedNode()
    tree.children.append(IndexedNode("where"))
    tree.children.append(IndexedNode("love"))
    tree.children.insert(1, IndexedNode("is"))
    tree.children.insert(2, IndexedNode("the"))
    tree.show("{0.index} has {0.data}")
    print(f"{tree.children=}")

    tree.children[3].index = 0
    tree.show("{0.index} has {0.data}")
    print(f"{tree.children=}")

main()
