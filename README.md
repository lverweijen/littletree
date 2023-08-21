LittleTree is a library that provides trees.
The package is purely written in python and tries to be easy to use, but operations are generally implemented in an efficient way.
It was created because all other tree implementations were either too basic, slow or complicated.

The package has taken much inspiration from anytree and itertree.
Compared to anytree, it should generally have better performance.
Compared to itertree, its implementation is much simpler and minimalistic.

## Example ##

A tree can be used in a similar way as a `dict`:

```python
from littletree import Node

tree = Node(identifier="World")
tree["Africa"] = Node()
tree["America"] = Node()
tree["Europe"] = Node()

print(tree.to_string())
tree.to_image('world.png')  # Works if dot(graphviz) is on path
```

The resulting tree looks like this:

```
 World
 ├── Asia
 ├── Africa
 ├── America
 └── Europe
```

![world](https://github.com/lverweijen/tree/main/world.png)

See [tutorial](https://github.com/lverweijen/tree/main/tutorial.md) for more information.

## Limitations ##
- Each node has a single parent
- A node can't have a sibling with the same identifier

## Alternatives ##

Before creating this, I looked at some other libraries.
Each had some things I liked and disliked.
None of them was exactly how I wanted it, so I decided to create something new.

- [anytree](https://github.com/c0fec0de/anytree) - Very hackable, but implementation uses lists, which makes lookups slow.
- [bigtree](https://github.com/kayjan/bigtree) - Similar to anytree, but has more features.
- [itertree](https://github.com/BR1py/itertree) - Has many features and is fast, but its design is complex.
- [treelib](https://github.com/caesar0301/treelib) - Puts all nodes of a tree into a single flat dict.
