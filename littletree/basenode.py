import sys
from typing import Mapping, Iterable, Union, Any, Generic, ValuesView, Tuple
from typing import TypeVar, Callable, Hashable, Optional

from littletree.tree import Tree
from .exceptions import DuplicateParentError, DuplicateChildError, LoopError
from .exporters import StringExporter, DotExporter, MermaidExporter
from .nodepath import NodePath
from .tree import NodeItem

TNode = TypeVar("TNode", bound="BaseNode")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)


class BaseNode(Generic[TIdentifier], Tree):
    """Minimalistic node class that a user can inherit from.

    Compared to Node this class is more primitive and less opinionated.
    This class is not made abstract, so it's possible to use a BaseNode directly.
    """
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
        """Create a Node

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
        """Check if two trees are equal.

        Trees are equal if they have the same structure.

        Change from version 0.5.0:
        - Two trees can now be equal if the roots have a different identifier.
        """
        if self is other:
            return True
        elif isinstance(other, self.__class__):
            return all(n1._cdict.keys() == n2._cdict.keys() for n1, n2 in self.iter_together(other))
        else:
            return NotImplemented

    def __getitem__(self, identifier: TIdentifier) -> TNode:
        """Get child by identifier."""
        return self._cdict[identifier]

    def __setitem__(self, new_identifier: TIdentifier, new_node: TNode):
        """Add child to this tree.

        If new_node already has a parent, throws UniqueParentError.
        To move an existing node use newtree["node"] = bound_node.detach()
        If new_node already has an identifier, it will be renamed.
        If a node with the same identifier exists, it will be detached first.

        :param new_identifier: Identifier for new node
        :param new_node: The node to add
        :return:
        """
        old_node = self._cdict.get(new_identifier)
        if new_node._parent:
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
        p = self._parent
        old_identifier = self._identifier
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
        old_parent = self._parent
        if old_parent is not new_parent:
            t = self._identifier
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

    @children.setter
    def children(self, new_children):
        old_children = list(self.children)
        self.clear()
        try:
            self.update(new_children)
        except LoopError as err:
            self.update(old_children)
            raise err from None

    @children.deleter
    def children(self):
        self.clear()

    @property
    def path(self) -> NodePath:
        try:
            return self._path
        except AttributeError:
            path = self._path = self.path_class(self)
            return path

    def update(
        self,
        other: Union[Mapping[TIdentifier, TNode], Iterable[TNode], TNode],
        mode: str = "copy",
        check_loop: bool = True,
    ) -> None:
        """Add multiple nodes at once.

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
                other_dict[node._identifier] = node
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

    def _update(self, other: Mapping[TIdentifier, TNode]):
        """Low-level update. Never use directly.

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

    def copy(self, _memo=None, keep=None) -> TNode:
        """Make a shallow copy or deepcopy if memo is passed."""
        return self.transform(lambda _node, _item: BaseNode(), keep=keep)

    def transform(self, f: Callable[[TNode, NodeItem], TNode], keep=None) -> TNode:
        """Make a modified copy of a tree.

        :param f: How to modify each node
        :param keep: Which node and children to include
        """
        other = f(self, NodeItem(0, 0))
        other._identifier = self._identifier
        insert_depth = 0
        for node, item in self.iter_descendants(keep=keep, with_item=True):
            while insert_depth >= item.depth:
                insert_depth -= 1
                other = other._parent
            other[node._identifier] = other = f(node, item)
            insert_depth += 1
        return other.root

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return self.copy(memo)

    def detach(self) -> TNode:
        """Remove node from its parent.

        This is especially useful when moving the node to a different tree or branch.
        :return: self
        """
        p = self._parent
        if p is not None:
            del p._cdict[self._identifier]
            self._parent = None
        return self

    def clear(self) -> None:
        """Remove all children."""
        for child in self.children:
            child._parent = None
        self._cdict.clear()

    def sort_children(
        self,
        key: Optional[Callable[[TNode], Any]] = None,
        recursive: bool = False,
        reverse: bool = False,
    ) -> None:
        """Sort children

        :param key: Function to sort by. If not given, sort on identifier.
        :param recursive: Whether all descendants should be sorted or just children.
        :param reverse: Whether to sort in reverse order
        :return: self
        """
        if key:
            nodes = sorted(self.children, key=key, reverse=reverse)
            self._cdict.clear()
            self._cdict.update((n._identifier, n) for n in nodes)
            if recursive:
                for d in self.iter_descendants():
                    nodes = sorted(d.children, key=key, reverse=reverse)
                    d._cdict.clear()
                    d._cdict.update((n._identifier, n) for n in nodes)
        else:
            nodes = sorted(self._cdict.items(), reverse=reverse)
            self._cdict.clear()
            self._cdict.update(nodes)
            if recursive:
                for d in self.iter_descendants():
                    nodes = sorted(d._cdict.items(), reverse=reverse)
                    d._cdict.clear()
                    d._cdict.update(nodes)

    def iter_together(self, other) -> Tuple[TNode, Optional[TNode]]:
        """Yield all nodes in self with similar nodes in other.

        If no equivalent node can be found in other, yield node from self with None
        """
        yield self, other
        stack = []
        for node, item in self.iter_descendants(with_item=True):
            while len(stack) >= item.depth:
                other = stack.pop(-1)
            if len(stack) < item.depth:
                stack.append(other)
                if other:
                    try:
                        other = other[node._identifier]
                    except KeyError:
                        other = None
            yield node, other

    def _check_integrity(self):
        """Recursively check integrity of each parent with its children.

        Used for testing purposes.
        """
        for child_identifier, child in self._cdict.items():
            assert child.identifier == child_identifier
            assert child.parent is self
            child._check_integrity()

    def show(self, formatter=None, style=None, keep=None):
        """Print this tree. Shortcut for print(tree.to_string())."""
        if sys.stdout:
            if not style:
                supports_unicode = not sys.stdout.encoding or sys.stdout.encoding.startswith('utf')
                style = "square" if supports_unicode else "ascii"
            self.to_string(sys.stdout, formatter=formatter, style=style, keep=keep)

    def to_string(self, file=None, formatter=None, style="square", keep=None) -> Optional[str]:
        """Convert tree to string."""
        exporter = StringExporter(formatter, style)
        return exporter.to_string(self, file, keep=keep)

    def to_image(
        self,
        file=None,
        keep=None,
        node_attributes=None,
        node_label=str,
        backend="graphviz",
        **kwargs
    ):
        """Convert tree to image."""
        if node_attributes is None:
            node_attributes = {"label": node_label}
        if backend == "graphviz":
            exporter = DotExporter(node_attributes=node_attributes, **kwargs)
        elif backend == "mermaid":
            exporter = MermaidExporter(node_label=node_label, **kwargs)
        else:
            raise ValueError(f"Backend should be graphviz or mermaid, not {backend}")
        return exporter.to_image(self, file, keep=keep)

    def to_dot(
        self,
        file=None,
        keep=None,
        node_attributes=None,
        node_label=str,
        **kwargs
    ) -> Optional[str]:
        """Convert tree to dot file."""
        if node_attributes is None:
            node_attributes = {"label": node_label}
        exporter = DotExporter(node_attributes=node_attributes, **kwargs)
        return exporter.to_dot(self, file, keep=keep)

    def to_mermaid(self, file=None, keep=None, node_label=str, **kwargs) -> Optional[str]:
        """Convert tree to mermaid file."""
        exporter = MermaidExporter(node_label=node_label, **kwargs)
        return exporter.to_mermaid(self, file, keep=keep)

    def _check_loop1(self, other: TNode):
        """Check if other is an ancestor of self."""
        if not other.is_leaf:
            if self is other:
                raise LoopError(self, other)
            if any(other is ancestor for ancestor in self.iter_ancestors()):
                raise LoopError(self, other)

    def _check_loop2(self, others: Iterable[TNode]):
        """Check if any of others is an ancestor of self."""
        ancestors = set(map(id, self.iter_ancestors()))
        ancestors.add(id(self))

        ancestor = next((child for child in others if id(child) in ancestors), None)
        if ancestor:
            raise LoopError(self, ancestor)
