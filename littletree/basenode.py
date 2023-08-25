import itertools
from collections import namedtuple
from collections.abc import ValuesView
from typing import Mapping, Iterable, Optional, Union, Any, Callable, Iterator, Generic, TypeVar, \
    Hashable, Tuple

from .exceptions import DuplicateParentError, DuplicateChildError, LoopError
from .nodepath import NodePath

TNode = TypeVar("TNode", bound="BaseNode")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)
NodePredicate = Callable[[TNode, "NodeItem"], bool]


class BaseNode(Generic[TIdentifier]):
    """This can serve as a base class (or even be used directly)"""
    __slots__ = "_identifier", "_parent", "_cdict", "_cvalues", "_path"

    # These can be changed in child classes
    dict_class = dict
    path_class = NodePath

    def __init__(
        self: TNode,
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
        self._identifier = identifier
        self._parent = parent
        self._cdict = self.dict_class()

        if children:
            if parent is not None:
                parent._check_loop2(children)
                if identifier in parent._cdict:
                    raise DuplicateChildError(parent, identifier)
            self.update(children, check_loop=False)

        if parent is not None:
            pdict = parent._cdict
            if identifier not in pdict:
                pdict[identifier] = self
            else:
                raise DuplicateChildError(parent, identifier)

    def __repr__(self) -> str:
        output = [self.__class__.__name__, f"({self.identifier!r})"]
        return "".join(output)

    def __eq__(self: TNode, other: TNode):
        if self is other:
            return True
        return self.identifier == other.identifier and self._cdict == other._cdict

    def __getitem__(self, identifier: TIdentifier) -> TNode:
        """Get child by identifier."""
        return self._cdict[identifier]

    def __setitem__(self, new_identifier: TIdentifier, new_node: TNode):
        """
        Add child to this tree.

        If new_node already has a parent, throws UniqueParentError.
        To move an existing node use newtree["node"] = bound_node.detach()
        If new_node already has an identifier, it will be renamed.
        If a node with the same identifier exists, it will be detached first.

        :param new_identifier: Identifier for new node
        :param new_node: The node to add
        :return:
        """
        old_node = self._cdict.get(new_identifier)
        if not new_node.is_root:
            if old_node is not new_node:
                raise DuplicateParentError(new_node)
        else:
            self._check_loop1(new_node)
            if old_node is not None:
                old_node._parent = None
            self._cdict[new_identifier] = new_node
            new_node._identifier = new_identifier
            new_node._parent = self

    def __delitem__(self, identifier: TIdentifier):
        """Remove a child from this tree."""
        node = self.pop(identifier)
        if node is None:
            raise KeyError(f"Node with {identifier} doesn't exist")

    def __contains__(self, identifier) -> bool:
        """Check if node with identifier exists."""
        return identifier in self._cdict

    __iter__ = None

    @property
    def identifier(self) -> Any:
        return self._identifier

    @identifier.setter
    def identifier(self, new_identifier):
        p = self.parent
        old_identifier = self.identifier
        if p is not None:
            if new_identifier in p._cdict:
                raise DuplicateChildError(new_identifier, p)
            else:
                del p._cdict[old_identifier]
                p._cdict[new_identifier] = self
        self._identifier = new_identifier

    @property
    def parent(self) -> TNode:
        return self._parent

    @parent.setter
    def parent(self, new_parent):
        old_parent = self.parent
        if old_parent is not new_parent:
            t = self.identifier
            if new_parent is None:
                self._parent = None
            elif t in new_parent:
                raise DuplicateChildError(t, new_parent)
            else:
                self._check_loop1(new_parent)
                new_parent._cdict[t] = self
                self._parent = new_parent
            if old_parent is not None:
                del old_parent._cdict[t]

    @parent.deleter
    def parent(self):
        self.detach()

    @property
    def children(self) -> ValuesView[TNode]:
        try:
            return self._cvalues
        except AttributeError:
            children = self._cvalues = self._cdict.values()
            return children

    @property
    def path(self) -> NodePath:
        try:
            return self._path
        except AttributeError:
            path = self._path = self.path_class(self)
            return path

    @property
    def root(self) -> TNode:
        """Return root of tree."""
        p, p2 = self, self.parent
        while p2:
            p, p2 = p2, p2.parent
        return p

    @property
    def is_leaf(self) -> bool:
        return not self._cdict

    @property
    def is_root(self) -> bool:
        return self._parent is None

    def update(
        self,
        other: Union[Mapping[TIdentifier, TNode], Iterable[TNode], TNode],
        mode: str = "copy",
        check_loop: bool = True,
    ) -> TNode:
        """
        Add multiple nodes at once and return self.

        This is much faster than setitem when adding multiple children at once.

        About time complexity:
        Let n be the number of nodes added, d be the depth of the tree, C be copy time
        T(n) = O(nC + d) if check_loop and not consume
        T(n) = O(n + d) if check_loop and (consume or no child has a parent)
        T(n) = O(nC) if not check_loop and not consume
        T(n) = O(n) if not check_loop and (consume or no child has a parent)

        :param other: Source of other nodes.
        Other could be:
        - mapping Keys will become new identifiers
        - iterable Nodes will be added
        - node Same as self.update(other.children) but implemented more efficiently.
        :param mode: How to handle nodes that already have a parent
        - "copy": These nodes will be copied and remain in old tree
        - "detach": These nodes will be detached from old tree
        :param check_loop: If True, raises LoopError if a cycle is created.
        :return: self
        """
        if mode not in ("copy", "detach"):
            raise ValueError('mode should be "copy" or "detach"')
        if isinstance(other, Mapping):
            if check_loop:
                self._check_loop2(other.values())
            if mode == "detach":
                for node in other.values():
                    node.detach()
            else:
                conflict_resolutions = dict()
                for identifier, node in other.items():
                    if node._parent is not None:
                        conflict_resolutions[identifier] = node.copy()
                    node._identifier = identifier
                if conflict_resolutions:
                    other = dict(other)  # Don't modify input arguments
                    other.update(conflict_resolutions)
            self._update(other)
        elif isinstance(other, Iterable):
            other_dict = dict()
            for node in other:
                if node._parent is not None:
                    node = node.copy() if mode == "copy" else node.detach()
                other_dict[node.identifier] = node
            if check_loop:
                self._check_loop2(other_dict.values())
            self._update(other_dict)
        elif isinstance(other, BaseNode):
            if check_loop:
                self._check_loop1(other)
            if mode == "copy":
                other = other.copy()
            other = other._cdict
            self._update(other)
            other.clear()
        else:
            raise TypeError("new_children should be mapping, iterable or other node")
        return self

    def _update(self, other: Mapping[TIdentifier, TNode]):
        """
        Low-level update. Never use directly.

        Assumptions:
        - key, identifier already matches
        - existing parents of nodes can be ignored
        """
        cdict = self._cdict
        for identifier, child in other.items():
            child._parent = self
            old_child = cdict.get(identifier)
            if old_child:
                old_child._parent = None
            cdict[identifier] = child

    def pop(self, identifier: TIdentifier) -> Optional[TNode]:
        """Remove and return node with identifier or None."""
        node = self._cdict.pop(identifier, None)
        if node is not None:
            node._parent = None
        return node

    def copy(self, _=None):
        return self.__class__(identifier=self.identifier,
                              children={k: v.copy() for (k, v) in self._cdict.items()})

    __copy__ = copy
    __deepcopy__ = copy

    def detach(self) -> TNode:
        """
        Remove node from its parent.

        This is especially useful when moving the node to a different tree or branch.
        :return: self
        """
        p = self._parent
        if p is not None:
            del p._cdict[self._identifier]
            self._parent = None
        return self

    def clear(self) -> TNode:
        """Remove all children."""
        for child in self.children:
            child._parent = None
        self._cdict.clear()
        return self

    def sort_children(
        self,
        key: Optional[Callable[[TNode], Any]] = None,
        recursive: bool = False,
        reverse: bool = False,
    ) -> TNode:
        """
        Sort children
        :param key: Function to sort by. If not given, sort on identifier.
        :param recursive: Whether all descendants should be sorted or just children.
        :param reverse: Whether to sort in reverse order
        :return: self
        """
        if key:
            nodes = sorted(self.children, key=key, reverse=reverse)
            self._cdict.clear()
            self._cdict.update((n.identifier, n) for n in nodes)
        else:
            nodes = sorted(self._cdict.items(), reverse=reverse)
            self._cdict.clear()
            self._cdict.update(nodes)
        if recursive:
            for c in self.children:
                c.sort_children(key=key, recursive=recursive, reverse=reverse)
        return self

    def iter_tree(
        self,
        keep: NodePredicate = None,
        order: str = "pre",
        with_item: bool = False,
    ) -> Union[Iterator[TNode], Iterator[Tuple[TNode, "NodeItem"]]]:
        """
        Iterate through all nodes of tree

        :param keep: Predicate whether to continue iterating at node
        :param order: Whether to iterate in pre/post or level-order
        :param with_item: Whether to yield (node, node_item) instead of just the node
        :return: All nodes.
        """
        item = NodeItem(0, 0)
        if not keep or keep(self, item):
            if order in ("pre", "level"):
                yield (self, item) if with_item else self
            yield from self.iter_descendants(keep, order=order, with_item=with_item)
            if order == "post":
                yield (self, with_item) if with_item else self

    def iter_ancestors(self) -> Iterator[TNode]:
        p = self.parent
        while p:
            yield p
            p = p.parent

    def iter_descendants(
        self,
        keep: NodePredicate = None,
        order: str = "pre",
        with_item: bool = False,
    ) -> Union[Iterator[TNode], Iterator[Tuple[TNode, "NodeItem"]]]:
        """
        Iterate through descendants

        :param keep: Predicate whether to continue iterating at node
        :param order: Whether to iterate in pre/post or level-order
        :param with_item: Whether to yield (node, node_item) instead of just the node
        :return: All descendants.
        """
        if order == "pre":
            descendants = self._iter_descendants_pre(keep)
        elif order == "post":
            descendants = self._iter_descendants_post(keep)
        elif order == "level":
            descendants = self._iter_descendants_level(keep)
        else:
            raise ValueError('order should be "pre", "post" or "level"')

        if with_item:
            return descendants
        return (node for (node, with_item) in descendants)

    def iter_siblings(self) -> Iterator[TNode]:
        """Return siblings."""
        if self.parent is not None:
            return (child for child in self._parent.children if child != self)
        else:
            return iter(())

    def iter_leaves(self) -> Iterator[TNode]:
        """Yield leaf nodes."""
        for node in self.iter_descendants():
            if node.is_leaf:
                yield node

    def _iter_descendants_pre(self, keep, _depth=1):
        for index, child in enumerate(self.children):
            item = NodeItem(index, _depth)
            if not keep or keep(child, item):
                yield child, item
                yield from child._iter_descendants_pre(keep=keep, _depth=_depth + 1)

    def _iter_descendants_post(self, keep, _depth=1):
        for index, child in enumerate(self.children):
            item = NodeItem(index, _depth)
            if not keep or keep(child, item):
                yield from child._iter_descendants_post(keep=keep, _depth=_depth + 1)
                yield child, item

    def _iter_descendants_level(self, keep):
        chain = itertools.chain
        nodes = ((child, NodeItem(index, 1)) for (index, child) in enumerate(self.children))
        try:
            while True:
                node, item = next(nodes)
                if not keep or keep(node, item):
                    yield node, item
                    next_nodes = [(child, NodeItem(index, item.depth + 1))
                                  for index, child in enumerate(node.children)]
                    nodes = chain(nodes, next_nodes)
        except StopIteration:
            pass

    def _check_integrity(self):
        """Recursively check integrity of each parent with its children.

        Used for testing purposes.
        """
        for child_identifier, child in self._cdict.items():
            assert child.identifier == child_identifier
            assert child.parent == self
            child._check_integrity()

    def _check_loop1(self, other: TNode):
        if not other.is_leaf:
            if self is other:
                raise LoopError(self, other)
            if any(other is ancestor for ancestor in self.iter_ancestors()):
                raise LoopError(self, other)

    def _check_loop2(self, others: Iterable[TNode]):
        ancestors = set(map(id, self.iter_ancestors()))
        ancestors.add(id(self))

        ancestor = next((child for child in others if id(child) in ancestors), None)
        if ancestor:
            raise LoopError(self, ancestor)


NodeItem = namedtuple("NodeItem", ["index", "depth"])
