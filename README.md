LittleTree is a library that provides a tree data structure to python.
The package is purely written in python.
It should be intuivive to use while performant.

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

And it creates the following image:

![world](world.png)

See [tutorial](https://github.com/lverweijen/littletree/blob/main/tutorial.md) for more information.

## Features ##

- Intuitive dict-like usage for creating and modifying trees.
- Performant implementation of common operations and tree traversals.
- Easy to subclass from. It's even possible to make it use a different dict backend ([indexed.Dict](https://pypi.org/project/indexed/), [SortedDict](https://grantjenks.com/docs/sortedcontainers/)).
- Can handle big trees even if they are 10,000 layers deep.
- Can be imported / exported to many different formats (nested dict, rows, relations, graphviz, mermaid, newick, networkx).

## Limitations ##
- Each node has at most one parent. (It's a tree not a graph)
- Different children of the same parent must have different names. (It's not a multidict)

See further:
[Pypi](https://pypi.org/project/littletree/) |
[Github](https://github.com/lverweijen/littletree) |
[Issues](https://github.com/lverweijen/littletree/issues)

