import itertools
from collections import namedtuple
from collections.abc import ValuesView
from typing import Mapping, Iterable, Optional, Union, Any, Callable, Iterator

from exceptions import DuplicateParent, DuplicateChild
from nodepath import NodePath


class Node:
    __slots__ = "_identifier", "_parent", "_cdict", "_cvalues", "_path"
    dict_class = dict  # Can be changed in child classes

    def __init__(
        self,
        identifier="node",
        parent: Optional["Node"] = None,
        children: Union[Mapping[Any, "Node"], Iterable["Node"]] = (),
    ):
        """
        Create a Node

        :param identifier: Identifier for this node
        :param parent: Parent if any
        :param children: Children if any
        """
        self._identifier = identifier
        self._parent = parent
        self._cdict = self.dict_class()

        if parent is not None:
            pdict = parent._cdict
            if identifier not in pdict:
                pdict[identifier] = self
            else:
                raise DuplicateChild(parent, identifier)

        if children:
            self.update(children)

    def __getitem__(self, identifier) -> "Node":
        """Get child by identifier."""
        return self._cdict[identifier]

    def __setitem__(self, new_identifier, new_node):
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
                raise DuplicateParent(new_node)
        else:
            if old_node is not None:
                old_node._parent = None

            self._cdict[new_identifier] = new_node
            new_node._identifier = new_identifier
            new_node._parent = self

    def __delitem__(self, identifier):
        """Remove a child from this tree."""
        node = self.pop(identifier)
        if node is None:
            raise KeyError(f"Node with {identifier} doesn't exist")

    def update(self, new_children: Union[Mapping[Any, "Node"], Iterable["Node"]]) -> "Node":
        """
        Add multiple nodes at once.

        None of the new nodes should already have a parent.
        If existing nodes have the same identifier, they will be detached.

        :param new_children: Nodes to add
        :return: self
        """
        cdict = self._cdict
        if isinstance(new_children, Mapping):
            # Error checking
            for new_child in new_children.values():
                if not new_child.is_root:
                    raise DuplicateParent(new_child)

            # No errors, perform update
            for identifier, new_child in new_children.items():
                new_child._identifier = identifier

                old_child = cdict.get(identifier)
                if old_child:
                    old_child._parent = None

                cdict[identifier] = new_child
        elif isinstance(new_children, Iterable):
            add_children = {}
            del_children = []

            # Error checking and gathering
            for new_child in new_children:
                if not new_child.is_root:
                    raise DuplicateParent(new_child)
                else:
                    identifier = new_child._identifier
                    old_child = cdict.get(identifier)
                    if old_child:
                        del_children.append(old_child)
                    add_children[identifier] = new_child

            # Perform actual updates
            for old_child in del_children:
                old_child._parent = None
            for new_child in new_children:
                new_child._parent = self

            cdict.update(add_children)

        return self

    def __contains__(self, identifier) -> bool:
        """Check if node with identifier exists."""
        return identifier in self._cdict

    def __repr__(self) -> str:
        output = [self.__class__.__name__, f"({self.identifier!r})"]
        return "".join(output)

    def pop(self, identifier) -> Optional["Node"]:
        """Remove and return node with identifier or None."""
        node = self._cdict.pop(identifier, None)
        if node is not None:
            node._parent = None
        return node

    @property
    def identifier(self) -> Any:
        return self._identifier

    @identifier.setter
    def identifier(self, new_identifier):
        p = self.parent
        old_identifier = self.identifier

        if p is not None:
            if new_identifier in p._cdict:
                raise DuplicateChild(new_identifier, p)
            else:
                del p._cdict[old_identifier]
                p._cdict[new_identifier] = self

        self._identifier = new_identifier

    @property
    def parent(self) -> "Node":
        return self._parent

    @parent.setter
    def parent(self, new_parent):
        old_parent = self.parent

        if old_parent is not new_parent:
            t = self.identifier

            if new_parent is None:
                self._parent = None
            elif t in new_parent:
                raise DuplicateChild(t, new_parent)
            else:
                new_parent._cdict[t] = self
                self._parent = new_parent

            if old_parent is not None:
                del old_parent._cdict[t]

    @parent.deleter
    def parent(self):
        self.detach()

    @property
    def children(self) -> ValuesView["Node"]:
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
            path = self._path = NodePath(self)
            return path

    @property
    def root(self) -> "Node":
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

    @property
    def level(self) -> int:
        """Return number of parents above."""
        result = 0
        p = self.parent
        while p:
            result += 1
            p = p.parent

        return result

    def copy(self, fields=()) -> "Node":
        """
        Return copy of node.

        The copy is deep downwards. The new copy won't have a parent by default.
        :param fields: Fields to pass to constructor if subclassing.
        :return: Copy of this node.
        """
        field_data = {field: getattr(self, field) for field in fields}
        new_node = self.__class__(**field_data)
        new_node.identifier = self.identifier
        new_node.update([child.copy() for child in self.children])
        return new_node

    def detach(self) -> "Node":
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

    def iter_children(self) -> Iterator["Node"]:
        return iter(self._cdict.values())

    def iter_ancestors(self) -> Iterator["Node"]:
        p = self.parent
        while p:
            yield p
            p = p.parent

    def iter_descendants(
        self,
        filter_: Optional[Callable] = None,
        post_order: bool = False,
        node_only: bool = True,
    ) -> Iterator[Union["Node", "NodeItem"]]:
        """
        Iterate through descendants

        :param filter_: Predicate whether to continue iterating at node
        :param post_order: Whether to iterate in post-order instead of pre-order
        :param node_only: Whether to return Node or NodeItem
        :return: All descendants.
        """
        if post_order:
            descendants = self._iter_descendants_post(filter_)
        else:
            descendants = self._iter_descendants_pre(filter_)

        if node_only:
            return (item.node for item in descendants)
        else:
            return descendants

    def iter_tree(
        self,
        filter_: Optional[Callable] = None,
        post_order: bool = False,
        node_only: bool = True
    ) -> Iterator[Union["Node", "NodeItem"]]:
        """
        Iterate through all nodes of tree

        :param filter_: Predicate whether to continue iterating at node
        :param post_order: Whether to iterate in post-order instead of pre-order
        :param node_only: Whether to return Node or NodeItem
        :return: All nodes.
        """
        self_item = NodeItem(0, 0, self)
        this_node = self if node_only else self_item

        if not filter_ or filter_(**self_item._asdict()):
            if not post_order:
                yield this_node

            yield from self.iter_descendants(filter_, post_order=post_order, node_only=node_only)

            if post_order:
                yield this_node

    def iter_siblings(self) -> Iterator["Node"]:
        """Return siblings."""
        if self.parent is not None:
            return (child for child in self._parent.iter_children() if child != self)
        else:
            return iter(())

    def iter_path(self) -> Iterator["Node"]:
        """Yield all nodes from root until itself."""
        return itertools.chain(reversed(tuple(self.iter_ancestors())), [self])

    def iter_leaves(self) -> Iterator["Node"]:
        """Yield leaf nodes."""
        for node in self.iter_descendants():
            if node.is_leaf:
                yield node

    def _iter_descendants_pre(self, filter_, _depth=0):
        _depth += 1

        for index, child in enumerate(self.iter_children()):
            item = NodeItem(index, _depth, child)
            if not filter_ or filter_(**item._asdict()):
                yield item
                yield from child._iter_descendants_pre(filter_=filter_, _depth=_depth)

    def _iter_descendants_post(self, filter_, _depth=0):
        _depth += 1

        for index, child in enumerate(self.iter_children()):
            item = NodeItem(index, _depth, child)
            if not filter_ or filter_(**item._asdict()):
                yield from child._iter_descendants_post(filter_=filter_, _depth=_depth)
                yield item

    def _check_integrity(self):
        """Recursively check integrity of node and descendants.

        Used for testing purposes.
        """
        for identifier, node in self._cdict.items():
            assert identifier == node.identifier
            node._check_integrity()


NodeItem = namedtuple("NodeItem", ["index", "level", "node"])
