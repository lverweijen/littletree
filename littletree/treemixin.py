import warnings
from abc import ABCMeta
from typing import TypeVar, Iterable

from abstracttree import print_tree, plot_tree, to_string, to_image, to_pillow, Route, Tree, \
    to_latex

from littletree.exceptions import LoopError

TNode = TypeVar("TNode", bound="TreeMixin")


class TreeMixin(Tree, metaclass=ABCMeta):
    __slots__ = ()

    def show(self, *args, **kwargs):
        """Print this tree. Shortcut for print(tree.to_string())."""
        print_tree(self, *args, **kwargs)

    def plot(self, *args, **kwargs):
        """Print this tree. Shortcut for print(tree.to_string())."""
        plot_tree(self, *args, **kwargs)

    def to_string(self, *args, **kwargs):
        """Convert tree to string."""
        return to_string(self, *args, **kwargs)

    def to_image(self, *args, **kwargs):
        """Convert tree to image."""
        return to_image(self, *args, **kwargs)

    def to_pillow(self, *args, **kwargs):
        """Convert tree to image."""
        return to_pillow(self, *args, **kwargs)

    def to_dot(self, *args, **kwargs):
        """Convert tree to dot file."""
        return to_dot(self, *args, **kwargs)

    def to_mermaid(self, *args, **kwargs):
        """Convert tree to mermaid file."""
        return to_image(self, *args, **kwargs)

    def to_latex(self, *args, **kwargs):
        """Convert tree to latex file."""
        return to_latex(self, *args, **kwargs)

    def iter_nodes(self, order="pre", keep=None, with_item=False):
        warnings.warn("This method is deprecated. Use tree.nodes instead.")
        nodes = self.nodes
        orders = {"pre": nodes.preorder,
                  "post": nodes.postorder,
                  "level": nodes.levelorder}
        if order_call := orders.get(order):
            items = order_call(keep)
        else:
            raise ValueError("Unknown order")

        if with_item:
            return items
        else:
            return (node for (node, _) in items)

    # Even older alias
    iter_tree = iter_nodes

    def iter_descendants(self, order="pre", keep=None, with_item=False):
        warnings.warn("This method is deprecated. Use tree.descendants instead.")
        nodes = self.descendants
        orders = {"pre": nodes.preorder,
                  "post": nodes.postorder,
                  "level": nodes.levelorder}
        if order_call := orders.get(order):
            items = order_call(keep)
        else:
            raise ValueError("Unknown order")

        if with_item:
            return items
        else:
            return (node for (node, _) in items)

    def iter_ancestors(self):
        warnings.warn("This method is deprecated. Use tree.ancestors instead.")
        return iter(self.ancestors)

    def iter_leaves(self):
        warnings.warn("This method is deprecated. Use tree.leaves instead.")
        return iter(self.leaves)

    def _check_loop1(self, other: TNode):
        """Check if other is an ancestor of self."""
        if not other.is_leaf:
            if self is other:
                raise LoopError(self, other)
            if any(other is ancestor for ancestor in self.ancestors):
                raise LoopError(self, other)

    def _check_loop2(self, others: Iterable[TNode]):
        """Check if any of others is an ancestor of self."""
        ancestors = set(map(id, self.ancestors))
        ancestors.add(id(self))

        ancestor = next((child for child in others if id(child) in ancestors), None)
        if ancestor:
            raise LoopError(self, ancestor)

    def to(self, *others):
        try:
            return Route(self, *others)
        except ValueError:
            return None
