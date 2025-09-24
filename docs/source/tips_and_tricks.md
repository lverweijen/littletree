# Tips and tricks #

## Accessing child nodes by index

To make child nodes accessible by index, install [indexed](https://pypi.org/project/indexed/):

```shell
pip install indexed
```

Then create a subclass of `Node` that uses `indexed.Dict` for its internal mapping:

```python
import indexed

class IndexedNode(Node):
    __slots__ = ()
    dict_class = indexed.Dict

tree = IndexedNode()
tree["Asia"] = IndexedNode()

assert tree.children[0] == tree["Asia"]
```

This works because `dict_class` can be set to any mapping type that behaves like `dict`.
The `children` property uses the [value-view](https://docs.python.org/3/library/stdtypes.html#dict-views) of the mapping.
In the case of `indexed.Dict`, this view additionally supports indexing.
As a result, `tree.children[0]` works as expected.

---

## Always-sorted child nodes

To ensure children are always sorted by their identifier, install [sortedcontainers](https://grantjenks.com/docs/sortedcontainers/):

```shell
pip install sortedcontainers
```

Then subclass `Node` to use `SortedDict`:

```python
from sortedcontainers import SortedDict

class SortedNode(Node):
    __slots__ = ()
    dict_class = SortedDict
    
    def sort_children(self, key=None):
        if key is not None:
            raise ValueError("Argument key is not supported. "
                             "Nodes are always sorted by identifier.")
        # No-op, since children are already sorted.

tree = SortedNode()
tree["b"] = SortedNode()
tree["c"] = SortedNode()
tree["a"] = SortedNode()

for child in tree.children:
    print(child.identifier)  # Prints "a", then "b", then "c"

# With a regular Node, children would appear in insertion order (b, c, a).
```

This works because `SortedDict` always keeps its items sorted by key.
Since `Node` uses the identifier as the key, the children are automatically sorted.
By contrast, iteration over a regular `dict` (and therefore a regular `Node`) follows insertion order.

---

## Node aliases with shared data

You can also create nodes that act as aliases of each other.
Aliases share the same `data` object, but may have different parents or children:

```python
class AliasNode(Node):
    __slots__ = "_aliases"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aliases = dict()

    def make_alias(self):
        new_alias = AliasNode(self.data)  # data is shared by reference
        self._aliases[id(new_alias)] = new_alias
        new_alias._aliases = self._aliases
        return new_alias

    @property
    def aliases(self):
        return [alias for alias in self._aliases.values() if alias is not self]


node1 = AliasNode({'info': 5})
node2 = node1.make_alias()

node2.data["more_info"] = 6
print(node2.data['info'])        # 5
print(node1.data['more_info'])   # 6

print(node1.aliases)  # [node2]
print(node2.aliases)  # [node1]
```

This works because the `data` parameter of `Node` is [passed by object reference](https://www.geeksforgeeks.org/python/pass-by-reference-vs-value-in-python/).
When multiple nodes are created with the same `data` object, they all share the same underlying dictionary.
This makes it possible to create aliases that stay in sync.

