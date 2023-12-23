import itertools
from abc import abstractmethod, ABCMeta
from collections import deque, namedtuple
from typing import TypeVar, Callable, Hashable, Union, Iterator, Tuple, Iterable, Optional

TNode = TypeVar("TNode", bound="BaseNode")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)
NodePredicate = Callable[[TNode, "NodeItem"], bool]


class NodeMixin(metaclass=ABCMeta):
    """Mixin that provides common tree methods and iterators.

    This class can be used instead of BaseNode,
    if you need to implement parent and children yourself.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def parent(self) -> Optional[TNode]:
        """Parent of this node or None if root."""
        raise NotImplementedError

    @property
    @abstractmethod
    def children(self) -> Iterable[TNode]:
        """Children of this node."""
        raise NotImplementedError

    @property
    def is_leaf(self) -> bool:
        return not self.children

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def root(self) -> TNode:
        """Return root of tree."""
        p, p2 = self, self.parent
        while p2:
            p, p2 = p2, p2.parent
        return p

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

    def iter_ancestors(self) -> Iterator[TNode]:
        """Yield parent, grandparent and further ancestors till root."""
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
        elif order == "post_rec":  # For checking if post returns correct result
            descendants = self._iter_descendants_post_rec(keep)
        else:
            raise ValueError('order should be "pre", "post" or "level"')

        if with_item:
            return descendants
        return (node for (node, with_item) in descendants)

    def iter_siblings(self) -> Iterator[TNode]:
        """Return siblings."""
        if self.parent is not None:
            return (child for child in self.parent.children if child is not self)
        else:
            return iter(())

    def iter_leaves(self) -> Iterator[TNode]:
        """Yield leaf nodes."""
        if self.is_leaf:
            yield self
        else:
            for node in self.iter_descendants():
                if node.is_leaf:
                    yield node

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

    def _iter_descendants_post_rec(self, keep, _depth=1):
        # Same as _iter_descendants_post (kept as reference implementation)
        for index, child in enumerate(self.children):
            item = NodeItem(index, _depth)
            if not keep or keep(child, item):
                yield from child._iter_descendants_post_rec(keep=keep, _depth=_depth + 1)
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

    def _iter_descendants_post(self, keep, _depth=1):
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
