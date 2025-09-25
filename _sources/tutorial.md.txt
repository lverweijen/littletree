# Tutorial

## Creating the root of the tree

A tree is represented by a `Node`. First, let's create the root:

```python
from littletree import Node

tree = Node({"population": 7.909}, identifier="World")
```

All nodes have the following attributes:

| Attribute    | Description                                            |
| ------------ | ------------------------------------------------------ |
| `identifier` | Identifier of the node. Must be unique among siblings. |
| `parent`     | Parent node. `None` for the root.                      |
| `children`   | Child nodes.                                           |
| `data`       | Dictionary for storing arbitrary data.                 |

---

## Adding nodes

You can add child nodes via assignment:

```python
tree["Asia"] = Node({"population": 4.694})
tree["Africa"] = Node({"population": 1.393})
```

Or by providing children or a parent in the constructor:

```python
# Adding children during creation
tree = Node(
    {"population": 7.909},
    identifier="World",
    children={
        "Asia": Node({"population": 4.694}),
        "Africa": Node({"population": 1.393})
    }
)

# Assigning a parent
Node({"population": 1.029}, identifier="America", parent=tree)
```

### Restrictions

* A node cannot have multiple parents:

```python
tree1 = Node()
tree2 = Node()
child = Node()

tree1["child"] = child  # OK
tree2["child"] = child  # Raises DuplicateParentError
```

Use `detach()` or `copy()` to reuse nodes:

```python
tree2["child"] = child.detach()  # Move node
tree2["child"] = child.copy()    # Copy node
```

* Sibling identifiers must be unique:

```python
tree = Node()
child1 = Node(identifier="name", parent=tree)
child2 = Node(identifier="name", parent=tree)  # DuplicateChildError
child2 = Node(identifier="different_name", parent=tree)  # OK
```

* Cycles are not allowed:

```python
tree = Node()
tree["child"] = tree  # LoopError
```

---

## Bulk adding

`update()` allows adding multiple children efficiently:

```python
tree.update({
    "Asia": Node({"population": 4.694}),
    "Africa": Node({"population": 1.393}),
})
```

You can copy or detach nodes from another tree:

```python
tree1 = Node(identifier="tree1")
tree2 = Node(identifier="tree2")

tree1["Asia"] = Node({"population": 4.694})

# Copy node from tree1 to tree2
tree2.update([tree1["Asia"]], mode="copy")

# Move node from tree1 to tree2
tree2.update([tree1["Asia"]], mode="detach")
```

---

## Iteration

Common iterators:

| Iterator                    | Description                          |
|-----------------------------|--------------------------------------|
| `iter(tree.children)`       | Iterate over children                |
| `iter(tree.path)`           | Iterate from root to self            |
| `iter(tree.nodes)`          | Iterate over all nodes               |
| `iter(tree.ancestors)`      | Iterate over ancestors               |
| `iter(tree.descendants)`    | Iterate over descendants             |
| `iter(tree.siblings)`       | Iterate over siblings                |
| `tree.iter_together(tree2)` | Iterate over multiple trees together |
| `iter(node1.to(node2))`     | Iterate from one node to another     |

The nodes can be iterated in a specific order.
Along with each node, an item is also yielded.
You can access `item.depth` to get the node's depth in the tree, and `item.index` to get its position among siblings at that level.

```python
for node, item in tree.nodes.preorder():
    ...

for node, item in tree.nodes.postorder():
    ...

for node, item in tree.nodes.levelorder():
    ...
```

Optional `keep` argument allows filtering nodes and their descendants:

```python
# Limit iteration to depth 2
for node, item in tree.nodes.preorder(keep=MaxDepth(2)):
    ...
```

---

## Path operations

Get the path to a node:

```python
str(tree["Europe"].path)  # "/World/Europe"
```

Access nodes using paths:

```python
lisbon = tree["Europe"]["Portugal"]["Lisbon"]  # Bracket style
lisbon = tree.path(["Europe", "Portugal", "Lisbon"])
lisbon = tree.path("Europe/Portugal/Lisbon")
```

Create nodes along a path if they don't exist:

```python
lisbon = tree.path.create(["Europe", "Portugal", "Lisbon"])
lisbon = tree.path.create("Europe/Portugal/Lisbon")
```

Search using glob patterns:

```python
lisbon_nodes = tree.path.glob("**/Lisbon")
```

---

## Miscellaneous tree operations

Height and breadth of the tree:

```python
height = tree.levels.count() - 1
breadth = tree.leaves.count()
```

Depth of a node:

```python
depth = node.ancestors.count()
```

Path from one node to another:

```python
madrid = tree.path.create("Europe/Spain/Madrid")
madrid_to_lisbon = list(madrid.to(lisbon))
```

Distance between nodes (edges):

```python
distance = madrid.to(lisbon).edges.count()
```

Lowest common ancestor:

```python
europe = madrid.to(lisbon).lca
```

---

## Exporting and serialization

| Function                                 | Description                        |
|------------------------------------------|------------------------------------|
| `to_string()`, `show()`                  | Pretty print the tree              |
| `plot()`                                 | Plot with matplotlib               |
| `to_dot()`, `to_mermaid()`, `to_latex()` | Export to dot, mermaid, or LaTeX   |
| `to_image()`, `to_pillow()`              | Requires Graphviz or Mermaid       |
| `from_dict()` / `to_dict()`              | Convert to/from JSON-like formats  |
| `from_rows()` / `to_rows()`              | Convert to/from path lists         |
| `from_relations()` / `to_relations()`    | Convert to/from parent-child lists |
| `from_newick()` / `to_newick()`          | Convert to/from Newick format      |
| `from_networkx()` / `to_networkx()`      | Convert to/from networkx graphs    |

Example using Newick format:

```python
family_newick = "((George, Charlotte, Louis)William,(Archie, Lilibet)Harry)'Charles III'[&&NHX:born=1948]"
family_tree = Node.from_newick(family_newick)
family_tree.show(style="round-arrow")
family_tree.to_pillow().show()  # Requires Graphviz and Pillow
family_tree.plot()  # Requires matplotlib
```

```text
Charles III
{'born': '1948'}
├→ William
│  ├→ George
│  ├→ Charlotte
│  ╰→ Louis
╰→ Harry
   ├→ Archie
   ╰→ Lilibet
```
![royals](images/royals.png)
