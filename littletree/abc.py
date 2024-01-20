import itertools
from abc import abstractmethod, ABCMeta
from collections import deque, namedtuple
from typing import TypeVar, Callable, Union, Iterator, Tuple, Optional, Collection, Literal, \
    overload, Iterable

TNode = TypeVar("TNode")
TMutDownNode = TypeVar("TMutDownNode", bound="MutableDownTree")
Order = Literal["pre", "post", "level"]
NodeItem = namedtuple("NodeItem", ["index", "depth"])
NodePredicate = Callable[[TNode, NodeItem], bool]


class AbstractTree(metaclass=ABCMeta):
    """Abstract baseclass for all trees."""
    __slots__ = ()

    @abstractmethod
    def has_child(self, node: TNode) -> bool:
        """Return whether node is a direct child of self."""
        raise NotImplementedError

    @abstractmethod
    def has_descendant(self, node: TNode) -> bool:
        """Return whether node is a descendant of self."""
        raise NotImplementedError

    def has_ancestor(self, node: TNode) -> bool:
        """Return whether node is an ancestor of self."""
        return node.has_descendant(self)


class UpTree(AbstractTree, metaclass=ABCMeta):
    """Abstract class for tree classes with parent but no children."""
    __slots__ = ()

    @property
    @abstractmethod
    def parent(self: TNode) -> Optional[TNode]:
        """Parent of this node or None if root."""
        return None

    @property
    def is_root(self) -> bool:
        """Return if this node is a root (has no parent)."""
        return self.parent is None

    @property
    def root(self) -> TNode:
        """Return root of tree."""
        p, p2 = self, self.parent
        while p2:
            p, p2 = p2, p2.parent
        return p

    def has_child(self, node: TNode) -> bool:
        return self is node.parent

    def has_descendant(self, node: TNode) -> bool:
        return any(self is ancestor for ancestor in node.iter_ancestors())

    def count_ancestors(self) -> int:
        """Count the number of ancestors.

        Also known as depth of this node.
        """
        return sum(1 for _ in self.iter_ancestors())

    def iter_ancestors(self) -> Iterator[TNode]:
        """Iterate ancestors from parent till root."""
        p = self.parent
        while p:
            yield p
            p = p.parent


class DownTree(AbstractTree, metaclass=ABCMeta):
    """Abstract class for tree classes with children but no parent."""
    __slots__ = ()

    @property
    @abstractmethod
    def children(self: TNode) -> Collection[TNode]:
        """Children of this node."""
        return ()

    @property
    def is_leaf(self) -> bool:
        """Return whether this node is a leaf (does not have children)."""
        return not self.children

    def has_child(self, node: TNode) -> bool:
        return any(node is child for child in self.children)

    def has_descendant(self, node: TNode) -> bool:
        return any(self is descendant for descendant in self.iter_descendants())

    def transform(self: TNode, f: Callable[[TNode], TMutDownNode]) -> TMutDownNode:
        """Return new tree where each node is transformed by f."""
        stack = []
        for node, item in self.iter_descendants(order='post', with_item=True):
            depth = item.depth
            while len(stack) < depth:
                stack.append(list())
            stack[depth - 1].append(new := f(node))
            if len(stack) > depth:
                new.add_children(stack.pop(-1))
        new = f(self)
        if stack:
            new.add_children(stack.pop())
        return new

    def count_leaves(self) -> int:
        """Count the number of leaves.

        This is also known as the breadth of the tree
        """
        return sum(1 for _ in self.iter_leaves())

    def iter_leaves(self) -> Iterator[TNode]:
        """Iterate through leaf nodes."""
        if self.is_leaf:
            yield self
        else:
            for node in self.iter_descendants():
                if node.is_leaf:
                    yield node

    def count_nodes(self) -> int:
        """Count the number of nodes in tree."""
        return 1 + self.count_descendants()

    @overload
    def iter_nodes(
            self,
            *,
            keep: NodePredicate = ...,
            order: Order = ...,
            with_item: Literal[False] = ...,
    ) -> Iterator[TNode]:
        ...

    @overload
    def iter_nodes(
            self,
            *,
            keep: NodePredicate = ...,
            order: Order = ...,
            with_item: Literal[True],
    ) -> Iterator[Tuple[TNode, NodeItem]]:
        ...

    @overload
    def iter_nodes(
            self,
            *,
            keep: NodePredicate = ...,
            order: Order = ...,
            with_item: bool,
    ) -> Union[Iterator[TNode], Iterator[Tuple[TNode, NodeItem]]]:
        ...

    def iter_nodes(self, *, keep=None, order: Order = "pre", with_item=False):
        """Iterate through all nodes of tree

        :param keep: Predicate whether to continue iterating at node
        :param order: Whether to iterate in pre/post or level-order
        :param with_item: Whether to yield (node, node_item) instead of just the node
        :return: All nodes.
        """
        item = NodeItem(0, 0)
        if not keep or keep(self, item):
            if order in ("pre", "level"):
                yield (self, item) if with_item else self
            yield from self.iter_descendants(keep=keep, order=order, with_item=with_item)
            if order == "post":
                yield (self, item) if with_item else self

    def count_descendants(self) -> int:
        """Count the number of descendants."""
        return sum(1 for _ in self.iter_descendants())

    @overload
    def iter_descendants(
            self,
            *,
            keep: NodePredicate = ...,
            order: Order = ...,
            with_item: Literal[False] = ...,
    ) -> Iterator[TNode]:
        ...

    @overload
    def iter_descendants(
            self,
            *,
            keep: NodePredicate = ...,
            order: Order = ...,
            with_item: Literal[True],
    ) -> Iterator[Tuple[TNode, NodeItem]]:
        ...

    @overload
    def iter_descendants(
            self,
            *,
            keep: NodePredicate = ...,
            order: Order = ...,
            with_item: bool,
    ) -> Union[Iterator[TNode], Iterator[Tuple[TNode, NodeItem]]]:
        ...

    def iter_descendants(self, *, keep=None, order: Order = "pre", with_item=False):
        """Iterate through descendants

        :param keep: Predicate whether to continue iterating at node
        :param order: Whether to iterate in pre/post or level-order
        :param with_item: Whether to yield (node, node_item) instead of just the node
        :return: All descendants.
        """
        try:
            f = self._ITERATION_METHODS[order]
        except KeyError:
            values = " or ".join(self._ITERATION_METHODS.keys())
            raise ValueError(f'order should be in {values}') from None
        else:
            descendants = f(self, keep)
            if with_item:
                return descendants
            return (node for (node, _) in descendants)

    def count_levels(self) -> int:
        """Count the number of levels.

        This is equal to height of the tree + 1
        """
        return 1 + max([item.depth for (_, item) in self.iter_nodes(with_item=True)])

    def iter_levels(self) -> Iterator[Iterator[TNode]]:
        """Iterate levels."""
        level = iter([self])
        level, output, test = itertools.tee(level, 3)
        while next(test, None):
            yield output
            level = (child for node in level for child in node.children)
            level, output, test = itertools.tee(level, 3)

    def _iter_descendants_pre(self, keep):
        nodes = deque((c, NodeItem(i, 1)) for (i, c) in enumerate(self.children))
        while nodes:
            node, item = nodes.popleft()
            if not keep or keep(node, item):
                yield node, item
                next_nodes = [(c, NodeItem(i, item.depth + 1))
                              for i, c in enumerate(node.children)]
                nodes.extendleft(reversed(next_nodes))

    def _iter_descendants_post(self, keep):
        children = iter([(c, NodeItem(i, 1)) for (i, c) in enumerate(self.children)])
        node, item = next(children, (None, None))
        stack = []

        while node or stack:
            # Go down
            keep_node = keep is None or keep(node, item)
            while keep_node and node.children:
                stack.append((node, item, children))
                children = iter([(c, NodeItem(i, item.depth + 1))
                                 for (i, c) in enumerate(node.children)])
                node, item = next(children)
                keep_node = keep is None or keep(node, item)
            if keep_node:
                yield node, item

            # Go right or go up
            node, item = next(children, (None, None))
            while node is None and stack:
                node, item, children = stack.pop()
                yield node, item
                node, item = next(children, (None, None))

    def _iter_descendants_level(self, keep):
        nodes = deque((c, NodeItem(i, 1)) for (i, c) in enumerate(self.children))
        while nodes:
            node, item = nodes.popleft()
            if not keep or keep(node, item):
                yield node, item
                next_nodes = [(c, NodeItem(i, item.depth + 1))
                              for i, c in enumerate(node.children)]
                nodes.extend(next_nodes)

    _ITERATION_METHODS = {"pre": _iter_descendants_pre,
                          "post": _iter_descendants_post,
                          "level": _iter_descendants_level}


class Tree(UpTree, DownTree, metaclass=ABCMeta):
    """Abstract class for tree classes with access to children and parents."""
    __slots__ = ()

    def count_siblings(self) -> int:
        """Count siblings."""
        if p := self.parent:
            return len(p.children) - 1
        return 0

    def iter_siblings(self) -> Iterator[TNode]:
        """Iterate through siblings."""
        if self.parent is not None:
            return (child for child in self.parent.children if child is not self)
        else:
            return iter(())


class MutableDownTree(DownTree, metaclass=ABCMeta):
    """Abstract class for mutable tree with children."""
    __slots__ = ()

    @abstractmethod
    def add_child(self, node: TNode):
        """Add node to children."""
        raise NotImplementedError

    @abstractmethod
    def remove_child(self, node: TNode):
        """Remove node from children."""
        raise NotImplementedError

    def add_children(self, children: Iterable[TNode]):
        """Add multiple nodes to children."""
        for child in children:
            self.add_child(child)


class MutableTree(Tree, MutableDownTree, metaclass=ABCMeta):
    """Abstract class for mutable tree with children and parent."""
    __slots__ = ()

    def detach(self) -> TNode:
        """Remove parent if any and return self."""
        if p := self.parent:
            p.remove_child(self)
        return self
