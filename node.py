import itertools
from collections import namedtuple
from typing import Mapping, Iterable

from exceptions import DuplicateParent, DuplicateChild
from nodepath import NodePath


class Node:
    __slots__ = "_identifier", "_parent", "_cdict", "_cvalues", "_path"
    dict_class = dict  # Can be changed in child classes

    def __init__(self, identifier="node", parent=None, children=()):
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

    def __getitem__(self, key):
        return self._cdict[key]

    def __setitem__(self, key, new_node):
        old_node = self._cdict.get(key)

        if not new_node.is_root:
            if old_node is not new_node:
                raise DuplicateParent(new_node)
        else:
            if old_node is not None:
                old_node._parent = None

            self._cdict[key] = new_node
            new_node._identifier = key
            new_node._parent = self
            return old_node

    def __delitem__(self, identifier):
        self._cdict.pop(identifier)

    def update(self, new_children):
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

    def __contains__(self, identifier):
        return identifier in self._cdict

    def __repr__(self):
        output = [self.__class__.__name__, f"({self.identifier})"]
        return "".join(output)

    def pop(self, identifier):
        node = self._cdict.pop(identifier, None)
        if node is not None:
            node._parent = None
        return node

    @property
    def identifier(self):
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
    def parent(self):
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
    def children(self):
        try:
            return self._cvalues
        except AttributeError:
            children = self._cvalues = self._cdict.values()
            return children

    @property
    def path(self):
        try:
            return self._path
        except AttributeError:
            path = self._path = NodePath(self)
            return path

    @property
    def root(self):
        p, p2 = self, self.parent
        while p2:
            p, p2 = p2, p2.parent

        return p

    @property
    def is_leaf(self):
        return not self._cdict

    @property
    def is_root(self):
        return self._parent is None

    @property
    def level(self):
        result = 0
        p = self.parent
        while p:
            result += 1
            p = p.parent

        return result

    def copy(self, fields=()):
        field_data = {field: getattr(self, field) for field in fields}
        new_node = self.__class__(**field_data)
        new_node.identifier = self.identifier
        new_node.update([child.copy() for child in self.children])
        return new_node

    def detach(self):
        p = self._parent
        if p is not None:
            del p._cdict[self._identifier]
            self._parent = None

        return self

    def iter_children(self):
        return iter(self._cdict.values())

    def iter_ancestors(self):
        p = self.parent
        while p:
            yield p
            p = p.parent

    def iter_descendants(self, filter_=None, post_order=False, node_only=True):
        if post_order:
            descendants = self._iter_descendants_post(filter_)
        else:
            descendants = self._iter_descendants_pre(filter_)

        if node_only:
            return (item.node for item in descendants)
        else:
            return descendants

    def iter_tree(self, filter_=None, post_order=False, node_only=True):
        this_node = self if node_only else NodeItem(0, 0, self)

        if not post_order:
            yield this_node

        yield from self.iter_descendants(post_order, filter_, node_only=node_only)

        if post_order:
            yield this_node

    def iter_siblings(self):
        if self.parent is not None:
            return (child for child in self._parent.iter_children() if child != self)
        else:
            return iter(())

    def iter_path(self):
        return itertools.chain(reversed(tuple(self.iter_ancestors())), [self])

    def iter_leaves(self):
        for node in self.iter_descendants():
            if node.is_leaf:
                yield node

    def _iter_descendants_pre(self, filter_, _depth=0):
        _depth += 1

        for index, child in enumerate(self.iter_children()):
            if not filter_ or filter_(child):
                yield NodeItem(index, _depth, child)
                yield from child._iter_descendants_pre(filter_=filter_, _depth=_depth)

    def _iter_descendants_post(self, filter_, _depth=0):
        _depth += 1

        for index, child in enumerate(self.iter_children()):
            if not filter_ or filter_(child):
                yield from child._iter_descendants_post(filter_=filter_, _depth=_depth)
                yield NodeItem(index, _depth, child)


NodeItem = namedtuple("NodeItem", ["index", "level", "node"])
