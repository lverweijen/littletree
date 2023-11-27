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
- Add MermaidExporter. Similar to DotExporter, but supported by [github](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).
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
 