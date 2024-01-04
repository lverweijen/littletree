LittleTree is a library that provides a tree data structure to python,
which is both fast and flexible.
It can be used to represent file systems, taxonomies and much more.

## Features ##

- Intuitive basic creation and modification of trees.
- Efficient implementation of common tree operations and traversals.
  Works on trees that are 10 000 layers deep.
- Extensible. Subclass `BaseNode` or `NodeMixin` if you need more freedom.
- Can be imported / exported to many different formats (nested dict, rows, relations, graphviz, mermaid, newick, networkx).
- Purely written in Python.

## Limitations ##
- Each node has at most one parent. (It's a tree not a graph!)
- Nodes cannot be their own ancestor.

## Installing ##

- Use [pip](https://pip.pypa.io/en/stable/getting-started/) to install littletree:

```sh
$ pip install --upgrade littletree
```
## Usage ##

A tree can be used in a similar way as a `dict`:

```python
from littletree import Node

tree = Node(identifier="World")
tree["Asia"] = Node()
tree["Africa"] = Node()
tree["America"] = Node()
tree["Europe"] = Node()

# Print tree to console
tree.show()

# Show tree as an image
tree.to_image().show()
```

The resulting tree is printed like this:

```
World
├─ Asia
├─ Africa
├─ America
└─ Europe
```

If [Pillow](https://pypi.org/project/pillow/) and [graphviz](https://graphviz.org/) are installed,
it will also display the following image:

![world](world.png)

See [tutorial](https://github.com/lverweijen/littletree/blob/main/tutorial.md) for more information.

See further:
[Pypi](https://pypi.org/project/littletree/) |
[Github](https://github.com/lverweijen/littletree) |
[Issues](https://github.com/lverweijen/littletree/issues)

