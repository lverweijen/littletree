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

    # Statistics
    def test_get_height(self):
        tree = self.tree
        node = self.tree.path('Europe/Finland/Helsinki/Helsinki')
        leaf = self.tree.path('Africa')
        self.assertEqual(5, tree.get_height())
        self.assertEqual(1, node.get_height())
        self.assertEqual(0, leaf.get_height())

    def test_get_depth(self):
        tree = self.tree
        node = self.tree.path('Europe/Finland/Helsinki/Helsinki')
        leaf = self.tree.path('Africa')
        self.assertEqual(0, tree.get_depth())
        self.assertEqual(4, node.get_depth())
        self.assertEqual(1, leaf.get_depth())

    def test_get_degree(self):
        tree = self.tree
        node = self.tree.path('Europe/Finland/Helsinki/Helsinki')
        leaf = self.tree.path('Africa')
        self.assertEqual(3, tree.get_degree())
        self.assertEqual(1, node.get_degree())
        self.assertEqual(0, leaf.get_degree())

    def test_get_index(self):
        tree = self.tree
        node = self.tree.path('Europe/Finland')
        leaf = self.tree.path('Africa')
        self.assertEqual(None, tree.get_index())
        self.assertEqual(2, node.get_index())
        self.assertEqual(1, leaf.get_index())

    # Special nodes
    def test_root(self):
        root = self.tree
        node = self.tree.path('Europe/Finland')
        leaf = self.tree.path('Africa')

        self.assertEqual(root, root.get_root())
        self.assertEqual(root, node.get_root())
        self.assertEqual(root, leaf.get_root())

    def test_lca(self):
        tree = self.tree
        europe = tree['Europe']
        norway = europe['Norway']
        stockholm = europe.path.get("Sweden/Stockholm")
        helsinki = europe.path.get('Finland/Helsinki')
        unknown = Node(identifier="unknown")

        self.assertEqual(europe, Node.lca(norway, stockholm, helsinki))
        self.assertEqual(europe, Node.lca(europe, norway, stockholm, helsinki))
        self.assertEqual(helsinki, Node.lca(helsinki, helsinki))
        self.assertEqual(None, Node.lca(helsinki, unknown))

    # Iterators
    def test_iter_children(self):
        result = [str(child.path) for child in self.tree.children]
        expected = ['/world/Europe', '/world/Africa']
        self.assertEqual(expected, result)

    def test_iter_tree1(self):
        result = [str(child.path) for child in self.tree.iter_tree()]
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

        result = [str(child.path) for child in self.tree.iter_tree(is_first_child)]
        expected = [
            '/world',
            '/world/Europe',
            '/world/Europe/Norway',
            '/world/Europe/Norway/Oslo',
        ]
        self.assertEqual(expected, result)

    def test_iter_tree3(self):
        target = self.tree
        result = [child.identifier for child in target.iter_tree(keep=lambda _, it: it.depth < 3,
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


if __name__ == '__main__':
    unittest.main()
