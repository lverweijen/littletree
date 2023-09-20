## Version 0.3.0 ##
- Remove `tree.show(img=True)`. Use `tree.to_image().show()` instead.
- New method `tree.transform()` that creates a modified or pruned copy of a tree.
- New method `tree.compare` that compares 2 nodes to each other.
- Rewrite `copy()` in terms of transform.
  Use `tree.copy()` for shallow copy.
  Use `tree.copy({})` for deep copy.
- Remove style `minimal`, but add style `list` for `tree.show()`.

## Version 0.2.3 ##
- Streamline DotExporter.
  Create temporary files in memory.
  Add option `as_bytes` to `to_image()`.
  Remove unused parameter `separator`.
- Add more default styles to StringExporter.
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
 