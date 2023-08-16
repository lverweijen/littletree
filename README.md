Tree implementation backed by `dict`.

This is simple tree library based on anytree and itertree.
Compared to anytree, key-based operations should generally execute much faster.
Compared to itertree, its implementation is much simpler.

## Example ##

A tree is used in a similar way as a `dict`:

```python
from dictree import Node

tree = Node(identifier="World")
tree["Africa"] = Node()
tree["America"] = Node()
tree["Europe"] = Node()

print(tree.to_string())
tree.to_image('world.png')  # Works if graphviz is on path
```

The resulting tree looks like this:

```
 Node('World')
 ├── Node('Africa')
 ├── Node('America')
 └── Node('Europe')
```

![world](world.png)

The Node class is very simple and it's possible to inherit from to create something more complex.

## Limitations ##
- Each node has a single parent
- A node can't have a sibling with the same identifier

## Alternatives ##

Before creating this, I looked at some other libraries.
Each had some things I liked and disliked.
None of them was exactly how I wanted it, so I decided to create something new.

- [anytree](https://github.com/c0fec0de/anytree) - Very hackable, but implementation uses lists, which slows some operations down.
- [bigtree](https://github.com/kayjan/bigtree) - Very similar to anytree. Has slightly more features.
- [itertree](https://github.com/BR1py/itertree) - Has many features, but its design is complex.
- [treelib](https://github.com/caesar0301/treelib) - Puts all nodes of a tree in a single dict, which makes some operations harder to achieve.
