import itertools
import operator
from fnmatch import fnmatchcase
from operator import methodcaller
from typing import Mapping, Iterable, Union, Any, Generic, ValuesView, Tuple
from typing import TypeVar, Callable, Hashable, Optional

from abstracttree import MutableTree

from abstracttree.mixins.views import PathView

from .exceptions import DuplicateParentError, DuplicateChildError, LoopError
from .treemixin import TreeMixin

TNode = TypeVar("TNode", bound="BaseNode")
TIdentifier = TypeVar("TIdentifier", bound=Hashable)


class BaseNode(Generic[TIdentifier], MutableTree, TreeMixin):
    """
    A basic tree node that can have a single parent and multiple children.

    The ``BaseNode`` forms the foundation for building hierarchical tree structures.
    Each node can be uniquely identified by its name within its parent's scope
    and can be navigated via ``NodePath`` objects.

    Compared to ``Node`` this class is more basic and useful for subclassing.
    """
    __slots__ = "_identifier", "_parent", "_cdict", "_cvalues"

    # These can be changed in child classes
    dict_class = dict

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

    def __getitem__(self, identifier: TIdentifier) -> TNode:
        """Get child by identifier."""
        return self._cdict[identifier]

    def __setitem__(self, new_identifier: TIdentifier, new_node: TNode):
        """Add child to this tree.

        If new_node already has a parent, throws ``DuplicateParentError``.
        To move an existing node use ``newtree["node"] = bound_node.detach()``.
        The new node will get the identifier given. If it already has an identifier, it will be renamed.
        If a node with the same identifier already exists, it will be detached.

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

    # Disabled, because python would default to an implementation that results in an error.
    # Not sure what it should even do, so it's left undefined.
    __iter__ = None

    @property
    def identifier(self) -> Any:
        """Key to identify this node. This can not be equal to an identifier of a sibling."""
        return self._identifier

    @identifier.setter
    def identifier(self, new_identifier):
        p = self._parent
        old_identifier = self._identifier
        if p is not None:
            if new_identifier in p._cdict:
                if new_identifier != old_identifier:
                    raise DuplicateChildError(new_identifier, p)
            else:
                del p._cdict[old_identifier]
                p._cdict[new_identifier] = self
        self._identifier = new_identifier

    @property
    def parent(self) -> Optional[TNode]:
        """Parent of this node or None."""
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
    def root(self) -> TNode:
        # Reimplemented for performance
        node, maybe_parent = self, self._parent
        while maybe_parent is not None:
            node, maybe_parent = maybe_parent, maybe_parent.parent
        return node

    @property
    def is_leaf(self) -> bool:
        # Reimplemented for performance
        return not self._cdict

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
    def path(self) -> "NodePath":
        """Path object for access to parent or navigating forward."""
        return NodePath(self)

    def add_child(self, node: TNode, check_loop: bool = True):
        """
        Add a single child node.

        The child's parent will be set to this node. A ``DuplicateChildError``
        is raised if another child with the same name already exists.
        A ``DuplicateParentError`` will be raised if this child already has a parent.

        :param node: Child to add.
        :param check_loop: Whether to check if adding child results in a loop.
        :return:
        """
        if node.is_root:
            identifier = node.identifier
            if identifier in self:
                raise DuplicateChildError(node, self)
            if check_loop and not node.is_leaf:
                self._check_loop1(node)
            self._cdict[identifier] = node
            node._parent = self
        else:
            raise DuplicateParentError(node)

    def remove_child(self, node: TNode):
        if node.parent is self:
            node.detach()
        else:
            raise ValueError("Not a child")

    def update(
        self,
        other: Union[Mapping[TIdentifier, TNode], Iterable[TNode], TNode],
        mode: str = "copy",
        check_loop: bool = True,
    ) -> None:
        """Add multiple nodes at once.

        This is faster than repeatedly calling setitem when adding many children at once.

        About time complexity:
        Let n be the number of nodes added, d be the depth of the tree, C be copy time:

        - T(n) = O(nC + d) if ``check_loop`` and not ``consume``;
        - T(n) = O(n + d) if ``check_loop`` and (``consume`` or no child has a parent);
        - T(n) = O(nC) if not ``check_loop`` and not ``consume``;
        - T(n) = O(n) if not ``check_loop`` and (``consume`` or no child has a parent).

        :param other: Source of other nodes.
            Other could be:

                - mapping Keys will become new identifiers
                - iterable Nodes will be added
                - node Same as self.update(other.children) but implemented more efficiently.
        :param mode: How to handle nodes that already have a parent:

            - "copy": These nodes will be copied and remain in old tree
            - "detach": These nodes will be detached from old tree
        :param check_loop: If True, raises LoopError if a cycle is created.
        :return: None
        """
        if mode == "copy":
            _release = methodcaller("copy")
        elif mode == "detach":
            _release = methodcaller("detach")
        else:
            raise ValueError('mode should be "copy" or "detach"')

        _cdict = self._cdict
        if isinstance(other, Mapping):
            if check_loop:
                self._check_loop2(other.values())
            for identifier, node in other.items():
                if old_child := _cdict.get(identifier):
                    old_child._parent = None
                if node._parent is not None:
                    node = _release(node)
                _cdict[identifier] = node
                node._identifier = identifier
                node._parent = self
        elif isinstance(other, Iterable):
            if check_loop:
                if not hasattr(other, '__len__'):
                    other = list(other)
                self._check_loop2(other)
            for node in other:
                identifier = node._identifier
                if old_child := _cdict.get(identifier):
                    old_child._parent = None
                if node._parent is not None:
                    node = _release(node)
                _cdict[identifier] = node
                node._parent = self
        elif isinstance(other, BaseNode):
            if check_loop:
                self._check_loop1(other)
            if mode == 'copy':
                other = other.copy()
            other = other._cdict
            for identifier, node in other.items():
                if old_child := _cdict.get(identifier):
                    old_child._parent = None
                node._parent = self
            _cdict.update(other)
            other.clear()
        else:
            raise TypeError("new_children should be mapping, iterable or other node")

    def pop(self, identifier: TIdentifier) -> Optional[TNode]:
        """Remove and return node with identifier or None."""
        node = self._cdict.pop(identifier, None)
        if node is not None:
            node._parent = None
        return node

    def copy(self, _memo=None, keep=None) -> TNode:
        """Make a shallow copy or deepcopy if memo is passed."""
        return self.transform(lambda node: BaseNode(identifier=node.identifier), keep=keep)

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
        """
        if key:
            nodes = sorted(self.children, key=key, reverse=reverse)
            self._cdict.clear()
            self._cdict.update((n._identifier, n) for n in nodes)
            if recursive:
                for d in self.descendants:
                    nodes = sorted(d.children, key=key, reverse=reverse)
                    d._cdict.clear()
                    d._cdict.update((n._identifier, n) for n in nodes)
        else:
            nodes = sorted(self._cdict.items(), reverse=reverse)
            self._cdict.clear()
            self._cdict.update(nodes)
            if recursive:
                for d in self.descendants:
                    nodes = sorted(d._cdict.items(), reverse=reverse)
                    d._cdict.clear()
                    d._cdict.update(nodes)

    def iter_together(self, other) -> Tuple[TNode, Optional[TNode]]:
        """Yield all nodes in self with similar nodes in other.

        If no equivalent node can be found in other, yield node from self with None
        """
        yield self, other
        stack = []
        for node, item in self.descendants.preorder():
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


class NodePath(PathView):
    __slots__ = ()

    # Can be overridden by child classes
    separator = "/"

    def __eq__(self, other):
        if not isinstance(other, NodePath):
            return False
        if self.count() != other.count():
            return False
        return all(s1.identifier == s2.identifier for s1, s2 in itertools.zip_longest(self, other))

    def __str__(self) -> str:
        separator = self.separator
        return separator + separator.join([str(node.identifier) for node in self])

    def __call__(self, path) -> TNode:
        """Navigate to a descendant.

        path should either be a string like "child/subchild/subsubchild"
        or a list like ["child", "subchild", "subsubchild"].
        """

        if isinstance(path, str):
            path = path.split(self.separator)
        node = self._node
        for segment in path:
            node = node._cdict[segment]
        return node

    def get(self, path) -> Optional[TNode]:
        """Like calling path, but return None if node is missing."""
        try:
            return self(path)
        except KeyError:
            return None

    def create(self, path) -> TNode:
        """Like get, but create missing nodes."""
        if isinstance(path, str):
            path = path.split(self.separator)

        node = self._node
        path = iter(path)

        try:
            for segment in path:
                node = node[segment]
        except KeyError:
            node = self._create_node(identifier=segment, parent=node)

            for segment in path:
                node = self._create_node(identifier=segment, parent=node)

        return node

    def _create_node(self, identifier, parent: TNode) -> TNode:
        """Subclasses can overwrite this if the construction of a Node is different."""
        node = self._node.__class__()
        node.identifier = identifier
        node.parent = parent
        return node

    def glob(self, path) -> Iterable[TNode]:
        """
        Find nodes by globbing patterns.

        For example to find all nodes that start with 'a':

        >>> node.path.glob("**/a*")
        """

        if isinstance(path, str):
            path = path.split(self.separator)

        nodes = {id(self._node): self._node}
        for segment in path:
            if segment == "**":
                nodes = {id(node): node
                         for candidate in nodes.values()
                         for node in candidate.nodes}
            elif segment == "":
                nodes = {id(node): node
                         for node in nodes.values()
                         if not node.is_leaf}
            elif self._is_pattern(segment):
                nodes = {id(node): node
                         for candidate in nodes.values()
                         for node in candidate.children
                         if fnmatchcase(str(node.identifier), segment)}
            else:
                nodes = {id(candidate[segment]): candidate[segment]
                         for candidate in nodes.values()
                         if segment in candidate}

        return nodes.values()

    @staticmethod
    def _is_pattern(segment) -> bool:
        """Check if segment is a pattern. If not direct access is much faster."""
        return isinstance(segment, str) and any(char in segment for char in "*?[")


# Apply a few optimisations
from abstracttree import generics as _generics

_generics.parent.register(BaseNode, operator.attrgetter("_parent"))
_generics.children.register(BaseNode, BaseNode.children.fget)
_generics.root.register(BaseNode, BaseNode.root.fget)
_generics.label.register(BaseNode, str)
_generics.nid.register(BaseNode, id)
