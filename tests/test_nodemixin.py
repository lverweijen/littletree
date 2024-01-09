import unittest

from littletree import Node


class TestNodeMixin(unittest.TestCase):
    def setUp(self) -> None:
        root = Node(identifier="world")
        root.path.create(["Europe", "Norway", "Oslo"])
        root.path.create(["Europe", "Sweden", "Stockholm"])
        root.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        root.path.create(["Africa"])

        self.tree = root

    # Special methods
    def test_root(self):
        root = self.tree
        node = self.tree.path('Europe/Finland')
        leaf = self.tree.path('Africa')

        self.assertEqual(root, root.root)
        self.assertEqual(root, node.root)
        self.assertEqual(root, leaf.root)

    # Iterators
    def test_iter_children(self):
        result = [str(child.path) for child in self.tree.children]
        expected = ['/world/Europe', '/world/Africa']
        self.assertEqual(expected, result)

    def test_iter_tree1(self):
        result = [str(child.path) for child in self.tree.iter_nodes()]
        expected = [
            '/world',
            '/world/Europe',
            '/world/Europe/Norway',
            '/world/Europe/Norway/Oslo',
            '/world/Europe/Sweden',
            '/world/Europe/Sweden/Stockholm',
            '/world/Europe/Finland',
            '/world/Europe/Finland/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki/Helsinki',
            '/world/Africa'
        ]
        self.assertEqual(expected, result)

    def test_iter_tree2(self):
        """Iterate only through nodes which are first-child."""
        def is_first_child(_, item):
            return item.index == 0

        result = [str(child.path) for child in self.tree.iter_nodes(is_first_child)]
        expected = [
            '/world',
            '/world/Europe',
            '/world/Europe/Norway',
            '/world/Europe/Norway/Oslo',
        ]
        self.assertEqual(expected, result)

    def test_iter_tree3(self):
        target = self.tree
        result = [child.identifier for child in target.iter_nodes(keep=lambda _, it: it.depth < 3,
                                                                  order="level")]
        expected = ['world', 'Europe', 'Africa', 'Norway', 'Sweden', 'Finland']
        self.assertEqual(expected, result)

    def test_iter_ancestors(self):
        target = self.tree.path(["Europe", "Norway", "Oslo"])
        result = [str(child.path) for child in target.iter_ancestors()]
        expected = ['/world/Europe/Norway', '/world/Europe', "/world"]
        self.assertEqual(expected, result)

    def test_iter_descendants1(self):
        target = self.tree.path(["Europe", "Finland"])
        result = [str(child.path) for child in target.iter_descendants(order="pre")]
        expected = [
            '/world/Europe/Finland/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki/Helsinki',
        ]
        self.assertEqual(expected, result)

    def test_iter_descendants_post1(self):
        target = self.tree
        result = [str(child.path) for child in target.iter_descendants(order="post")]

        expected = [
            '/world/Europe/Norway/Oslo',
            '/world/Europe/Norway',
            '/world/Europe/Sweden/Stockholm',
            '/world/Europe/Sweden',
            '/world/Europe/Finland/Helsinki/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki',
            '/world/Europe/Finland',
            '/world/Europe',
            '/world/Africa']
        self.assertEqual(expected, result)

    def test_iter_descendants_post2(self):
        target = self.tree.path(["Europe", "Finland"])
        result = [str(child.path) for child in target.iter_descendants(order="post")]
        expected = [
            '/world/Europe/Finland/Helsinki/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki',
        ]
        self.assertEqual(expected, result)

    def test_iter_descendants_post3(self):
        def keep_square(_, item):
            return item.index <= 2 and item.depth <= 2
        target = self.tree
        result = [str(child.path) for child in target.iter_descendants(keep_square, order="post")]
        expected = [
            '/world/Europe/Norway',
            '/world/Europe/Sweden',
            '/world/Europe/Finland',
            '/world/Europe',
            '/world/Africa',
        ]
        self.assertEqual(expected, result)

    def test_iter_descendants3(self):
        target = self.tree.path(["Europe", "Finland"])
        result = [str(child.path) for child in target.iter_descendants(order="level")]
        expected = [
            '/world/Europe/Finland/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki/Helsinki',
        ]
        self.assertEqual(expected, result)

    def test_iter_siblings(self):
        target = self.tree.path(["Europe", "Finland"])
        result = [str(child.path) for child in target.iter_siblings()]
        expected = ['/world/Europe/Norway', '/world/Europe/Sweden']
        self.assertEqual(expected, result)

        tree = Node()
        for child in ['child', 'twin1', 'twin2', 'twin3']:
            tree.path.create(child)
        result = [str(child.identifier) for child in tree['child'].iter_siblings()]
        expected = ['twin1', 'twin2', 'twin3']
        self.assertEqual(expected, result)

        # No siblings
        result = [str(child.path) for child in tree.iter_siblings()]
        expected = []
        self.assertEqual(expected, result)

    def test_iter_path(self):
        target = self.tree.path(["Europe", "Norway", "Oslo"])
        result = [str(node.path) for node in target.path]
        expected = ['/world', '/world/Europe', '/world/Europe/Norway', '/world/Europe/Norway/Oslo']
        self.assertEqual(expected, result)

    def test_iter_leaves(self):
        target = self.tree.path(["Europe"])
        result = [child.identifier for child in target.iter_leaves()]
        expected = ['Oslo', 'Stockholm', 'Helsinki']
        self.assertEqual(expected, result)

        leaf = self.tree.path('Africa')
        result = [child.identifier for child in leaf.iter_leaves()]
        expected = ['Africa']
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
