## Version 0.8.0 ##
- Package is now based on [AbstractTree](https://github.com/lverweijen/AbstractTree).
  The API has been revamped:
  - Methods `tree.iter_nodes` and similar renamed to `iter(tree.nodes)`
  - Methods `tree.count_nodes` and similar renamed to `tree.nodes.count()`
  - Method `Node.to_image()` now returns `bytes`. Use `Node.to_pillow` to get an image.
  - `littletree.export.*` is gone. Use `abstracttree.export.*` or `TreeMixin.*` instead.
  - Methods `add_child`, `add_children` and `remove_child` have been added to `BaseNode`.
- Rename `NodeMixin` to `TreeMixin`
- Move `BaseNode.path.to` to `TreeMixin.to`
- New methods:
  - `Node.from_tree`, a generic method to import almost anything

## (Scrapped) version 0.7.0 ##
- `NodeMixin` is gone. Instead `littletree.abc` contains multiple abstract classes.
- Rename `tree.iter_tree()` to `tree.iter_nodes()`.
- Some new methods:
  - `count` methods such as `count_nodes()`, `count_descendants()`
  - `add_child` and `remove_child` to add a node without changing identifier
  - `has_child`, `has_descendant`, `has_ancestor`

## Version 0.6.2 ##
- Make better use of NodeMixin
- Make sure most exporter work directly on NodeMixin
- Move exporter functions (from Node) directly to NodeMixin.

## Version 0.6.1 ##
- Remove `PathTo` class.
- Add class `Route` which is a generic version of the old `PathTo` class.

## Version 0.6.0 ##
- Add `NodeMixin` class, which provides something even more basic than `BaseNode`.
- Add parameters `keep` and `deep` to `tree.copy()`.
  So a pruned copy can be made by doing `tree.copy(keep=MaxDepth(3))`.
- Calling `iter_leaves` on a node that is a leaf
  now correctly yields an iterable containing just that Node.
- Fix `iter_siblings` to use identity instead of equality.
- Methods `sort_children`, `update` and `clear` no longer return `self`, but None.

## Version 0.5.1 ##
- Remove dataclasses (slots). Doesn't work until python3.10.
- Improve RowSerializer for pandas dataframe.
- Add newlines to output of `node.to_dot()` and `node.to_mermaid()`.

## Version 0.5.0 ##
- Add `NetworkXSerializer` for conversion to and from [networkx](https://networkx.org/).
- Faster implementation of `__eq__` for deep trees.
- Two trees can now be equal (`==`) if their roots have a different identifier. 
- Replace argument `str_factory` by `formatter` in `tree.show()` and `tree.to_string`.
  If passed a string, it will be applied as `formatter.format(node=node)`.

## Version 0.4.1 ##
Fix bug in `tree.compare` method

## Version 0.4.0 ##
- Improve DotExporter
  - Rename `name_factory` to `node_name`.
  - Derive file type from file extension if possible. Fall back on png.
  - Add `graph_attributes`.
  - Make attribute handling more intelligent. Distinguish static and dynamic properties.
  - Add parameter `directed` (default: True).
  - Remove whitespace around arrows for compacter file size.
- Add MermaidExporter. Similar to DotExporter, but supported by [GitHub](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).
- Make `tree.children` writable for more compatibility with anytree/bigtree
- Add parameters `backend` and `node_label` to `tree.to_image()`

## Version 0.3.0 ##
- Remove `tree.show(img=True)`. Use `tree.to_image().show()` instead.
- New method `tree.transform()` that creates a modified or pruned copy of a tree.
- New method `tree.compare()` that compares different trees to each other.
- Rewrite `copy()` in terms of transform.
  Use `tree.copy()` for shallow copy.
  Use `tree.copy({})` for deep copy.
- Remove style `minimal`, but add style `list` for `tree.show()`.
- Add option `escape_comments` to newick serializer to escape newick modifiers in node data.
- For now use `distance` and `comment` instead of `distance_field` and `comment_field` in NewickSerializer.
- Changed default format of `to_dict` to contain `identifier`.
- Rewrite RowSerializer
- Refactor RelationSerializer

## Version 0.2.3 ##
- Streamline `DotExporter`.
  Create temporary files in memory.
  Add option `as_bytes` to `to_image()`.
  Remove unused parameter `separator`.
- Add more default styles to `StringExporter`.
  Some have been renamed. `const` has been renamed to `square`.
- Simplify signature of `from_newick`. It accepts a string.
  For files a Path or file object should be passed.
- Add `tree.show()` for quickly rendering a tree to console.
  Same as `print(tree.to_string())`.

## Version 0.2.2 ##
- Make dictserialization work on large trees.

## Version 0.2.1 ##
- Improve newick serialization. It's much faster now and works on big trees.
- Because of how it is implemented, it now also works on preorder format `A(b, c)`, even though the standard form is `(b, c)A`.

## Version 0.2.0 ##
- Add `node.path.to`
- Remove `node.height()`. Tutorial shows alternative one-liner.
- Fix bug in post-order iteration
- Fix bug in `copy` and `deepcopy`
- Add support for serializing to and from [Newick format](https://evolution.genetics.washington.edu/phylip/newicktree.html)
 