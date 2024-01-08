import itertools
from abc import abstractmethod, ABCMeta
from collections import deque, namedtuple
from typing import TypeVar, Callable, Union, Iterator, Tuple, Iterable, Optional

TNode = TypeVar("TNode")
NodePredicate = Callable[[TNode, "NodeItem"], bool]


class UpTree(metaclass=ABCMeta):
    """Abstract class for tree classes with parent but no children."""
    __slots__ = ()

    @property
    @abstractmethod
    def parent(self) -> Optional[TNode]:
        """Parent of this node or None if root."""
        raise NotImplementedError

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

    def count_ancestors(self) -> int:
        """Count the number of ancestors.

        Also known as depth of this node.
        """
        return sum(1 for _ in self.iter_ancestors())

    def iter_ancestors(self) -> Iterator[TNode]:
        """Yield parent, grandparent and further ancestors till root."""
        p = self.parent
        while p:
            yield p
            p = p.parent


class DownTree(metaclass=ABCMeta):
    """Abstract class for tree classes with children but no parent."""
    __slots__ = ()

    @property
    @abstractmethod
    def children(self) -> Iterable[TNode]:
        """Children of this node."""
        raise NotImplementedError

    @property
    def is_leaf(self) -> bool:
        """Return if this node is a leaf (does not have children)."""
        return not self.children

    def count_nodes(self) -> int:
        """Count the number of nodes in tree."""
        return 1 + self.count_descendants()

    def iter_tree(
        self,
        keep: NodePredicate = None,
        order: str = "pre",
        with_item: bool = False,
    ) -> Union[Iterator[TNode], Iterator[Tuple[TNode, "NodeItem"]]]:
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
            yield from self.iter_descendants(keep, order=order, with_item=with_item)
            if order == "post":
                yield (self, item) if with_item else self

    def count_descendants(self) -> int:
        """Count the number of descendants."""
        return sum(1 for _ in self.iter_descendants())

    def iter_descendants(
        self,
        keep: NodePredicate = None,
        order: str = "pre",
        with_item: bool = False,
    ) -> Union[Iterator[TNode], Iterator[Tuple[TNode, "NodeItem"]]]:
        """Iterate through descendants

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

    def count_leaves(self) -> int:
        """Count the number of leaves.

        This is also known as the breadth of the tree
        """
        return sum(1 for _ in self.iter_leaves())

    def iter_leaves(self) -> Iterator[TNode]:
        """Yield leaf nodes."""
        if self.is_leaf:
            yield self
        else:
            for node in self.iter_descendants():
                if node.is_leaf:
                    yield node

    def count_levels(self) -> int:
        """Count the number of levels.

        This is equal to height of the tree + 1
        """
        return 1 + max([item.depth for (_, item) in self.iter_tree(with_item=True)])

    def iter_levels(self) -> Iterator[Iterator[TNode]]:
        """Iterate levels."""
        level = iter([self])
        level, output, test = itertools.tee(level, 3)
        while next(test, None):
            yield output
            level = (child for node in level for child in node.children)
            level, output, test = itertools.tee(level, 3)

    def _iter_descendants_pre(self, keep):
        nodes = deque((child, NodeItem(index, 1)) for (index, child) in enumerate(self.children))
        while nodes:
            node, item = nodes.popleft()
            if not keep or keep(node, item):
                yield node, item
                next_nodes = [(child, NodeItem(index, item.depth + 1))
                              for index, child in enumerate(node.children)]
                nodes.extendleft(reversed(next_nodes))

    def _iter_descendants_post(self, keep, _depth=1):
        # Same as _iter_descendants_post (kept as reference implementation)
        for index, child in enumerate(self.children):
            item = NodeItem(index, _depth)
            if not keep or keep(child, item):
                yield from child._iter_descendants_post(keep=keep, _depth=_depth + 1)
                yield child, item

    def _iter_descendants_level(self, keep):
        nodes = deque((child, NodeItem(index, 1)) for (index, child) in enumerate(self.children))
        while nodes:
            node, item = nodes.popleft()
            if not keep or keep(node, item):
                yield node, item
                next_nodes = [(child, NodeItem(index, item.depth + 1))
                              for index, child in enumerate(node.children)]
                nodes.extend(next_nodes)


class Tree(UpTree, DownTree, metaclass=ABCMeta):
    """Abstract class for tree classes with access to children and parents."""
    __slots__ = ()

    def count_siblings(self) -> int:
        """Count siblings."""
        return len(self.parent.children) - 1

    def iter_siblings(self) -> Iterator[TNode]:
        """Return siblings."""
        if self.parent is not None:
            return (child for child in self.parent.children if child is not self)
        else:
            return iter(())

    def _iter_descendants_post(self, keep, _depth=1):
        # Fast iterative version that requires parent
        nodes = iter([(child, NodeItem(index, 1))
                      for (index, child) in enumerate(self.children)])
        node, item = next(nodes, (None, None))
        stack = []

        while node or stack:
            # Go down
            keep_node = (keep is None or keep(node, item))
            while keep_node and node.children:
                children = iter([(child, NodeItem(index, item.depth + 1))
                                 for (index, child) in enumerate(node.children)])
                stack.append((item, nodes))
                node, item = next(children)
                nodes = children
                keep_node = (keep is None or keep(node, item))
            if keep_node:
                yield node, item

            # Go right or go up
            parent = node.parent
            node, item = next(nodes, (None, None))
            while node is None and stack:
                node = parent
                item, nodes = stack.pop()
                yield node, item
                parent = node.parent
                node, item = next(nodes, (None, None))


NodeItem = namedtuple("NodeItem", ["index", "depth"])
