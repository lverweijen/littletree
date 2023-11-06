import copy
from unittest import TestCase

from littletree import Node
from littletree.exceptions import LoopError


class TestNode(TestCase):
    def setUp(self) -> None:
        root = Node(identifier="world")
        root.path.create(["Europe", "Norway", "Oslo"])
        root.path.create(["Europe", "Sweden", "Stockholm"])
        root.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        root.path.create(["Africa"])

        self.tree = root

    def test_item(self):
        self.tree["South-America"] = Node(identifier="old_name")
        self.assertEqual("South-America", self.tree["South-America"].identifier)
        self.tree._check_integrity()

    def test_item_rename(self):
        self.tree["South-America"] = Node(identifier="old_name")
        self.tree["South-America"].identifier = "Sur-America"
        self.assertEqual("Sur-America", self.tree["Sur-America"].identifier)

        with self.assertRaises(KeyError):
            self.tree["South-America"]  # noqa

        self.tree._check_integrity()

    def test_update_dict(self):
        """Test with a dictionary."""
        self.tree.update({"Antarctica": Node()})
        self.assertEqual(self.tree["Antarctica"].identifier, "Antarctica")
        self.tree._check_integrity()

    def test_update_iterable(self):
        """Test with an iterable."""
        self.tree.update([Node(identifier="Antarctica")])
        self.assertEqual(self.tree["Antarctica"].identifier, "Antarctica")
        self.tree._check_integrity()

    def test_update_node1(self):
        """Test with another node."""
        tree = self.tree
        other_tree = Node(identifier='rest_of_world')
        other_tree['America'] = Node()
        other_tree['Asia'] = Node()
        other_tree['Australia'] = Node()

        tree.update(other_tree, mode="copy")
        tree._check_integrity()
        other_tree._check_integrity()

        result = [child.identifier for child in self.tree.children]
        expected = ['Europe', 'Africa', 'America', 'Asia', 'Australia']

        self.assertFalse(other_tree.is_leaf)
        self.assertEqual(expected, result)

    def test_update_node_consume(self):
        tree = self.tree
        other_tree = Node(identifier='rest_of_world')
        other_tree['America'] = Node()
        other_tree['Asia'] = Node()
        other_tree['Australia'] = Node()

        # Now that other world is going to collapse into ours
        tree.update(other_tree, mode="detach")
        tree._check_integrity()
        other_tree._check_integrity()

        result = [child.identifier for child in self.tree.children]
        expected = ['Europe', 'Africa', 'America', 'Asia', 'Australia']

        self.assertTrue(other_tree.is_leaf)
        self.assertEqual(expected, result)

    def test_reassign_children(self):
        tree = self.tree
        children = list(tree.children)
        children = reversed(children)
        tree.children = children
        tree.show()
        result = [str(child.path) for child in tree.children]
        expected = ['/world/Africa', '/world/Europe']
        self.assertEqual(expected, result)

    def test_reassign_children_error(self):
        with self.assertRaises(LoopError):
            self.tree['Europe'].children = [self.tree.root]

    def test_sort_children1(self):
        tree = self.tree
        tree.sort_children()
        tree._check_integrity()
        result = [str(child.path) for child in tree.children]
        expected = ['/world/Africa', '/world/Europe']
        self.assertEqual(expected, result)

    def test_sort_children2(self):
        tree = self.tree
        tree.sort_children(key=lambda node: len(node.children), recursive=True)
        tree._check_integrity()
        result = [str(child.path) for child in tree.iter_descendants()][:5]
        expected = ['/world/Africa',
                    '/world/Europe',
                    '/world/Europe/Norway',
                    '/world/Europe/Norway/Oslo',
                    '/world/Europe/Sweden']
        self.assertEqual(expected, result)

    def test_item_update_swap(self):
        """Swapping Europe and Africa. This is crazy."""
        tree = self.tree
        tree["Europe"], tree["Africa"] = tree["Africa"].detach(), tree["Europe"].detach()
        self.assertEqual("Norway", tree.path(["Africa", "Norway"]).identifier)
        tree._check_integrity()

    def test_clear(self):
        self.tree.clear()
        self.tree._check_integrity()
        self.assertTrue(self.tree.is_leaf)

    def test_compare(self):
        """Compare to nodes to one another."""
        tree = Node(identifier='world')
        tree['Europe'] = Node(data="first")
        tree['Africa'] = Node('very big')
        other_tree = Node(identifier='rest_of_world')
        other_tree['Europe'] = Node(data="something great")
        other_tree['Asia'] = Node()
        other_tree['Australia'] = Node(data="here be kangaroos")
        compare_tree = tree.compare(other_tree, keep_equal=True)
        result = compare_tree.to_string()
        expected = ('world\n'
                    "{'self': {}, 'other': {}}\n"
                    '├─ Europe\n'
                    "│  {'self': 'first', 'other': 'something great'}\n"
                    '├─ Africa\n'
                    "│  {'self': 'very big'}\n"
                    '├─ Asia\n'
                    "│  {'other': {}}\n"
                    '└─ Australia\n'
                    "   {'other': 'here be kangaroos'}\n")
        self.assertEqual(expected, result)

    def test_compare_self(self):
        compare_tree = self.tree.compare(self.tree)
        self.assertIsNone(compare_tree)

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

    def test_copy(self):
        europe = self.tree["Europe"]
        shallow_copy = copy.copy(europe)
        deep_copy = copy.deepcopy(europe)

        shallow_copy._check_integrity()
        deep_copy._check_integrity()

        self.assertEqual(europe, shallow_copy)
        self.assertEqual(europe, deep_copy)
