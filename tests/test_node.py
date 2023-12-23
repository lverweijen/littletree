import copy
from unittest import TestCase

from littletree import Node, MaxDepth
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
        self.assertEqual(self, self)

    def test_iter_together(self):
        tree = Node(identifier='world')
        tree['Europe'] = Node(data="first")
        tree['Africa'] = Node('very big')
        copy_tree = tree.copy()
        copy_tree.identifier = "world_copy"
        other_tree = Node(identifier='rest_of_world')
        other_tree['Europe'] = Node(data="something great")
        other_tree['Asia'] = Node()
        other_tree['Australia'] = Node(data="here be kangaroos")
        result = [(n1.identifier, n2 and n2.identifier)
                  for n1, n2 in tree.iter_together(other_tree)]
        result2 = [(n1.identifier, n2 and n2.identifier)
                   for n1, n2 in other_tree.iter_together(tree)]
        result3 = [(n1.identifier, n2 and n2.identifier)
                   for n1, n2 in tree.iter_together(copy_tree)]
        expected = [('world', 'rest_of_world'), ('Europe', 'Europe'), ('Africa', None)]
        expected2 = [('rest_of_world', 'world'),
                     ('Europe', 'Europe'),
                     ('Asia', None),
                     ('Australia', None)]
        expected3 = [('world', 'world_copy'), ('Europe', 'Europe'), ('Africa', 'Africa')]
        self.assertEqual(expected, result)
        self.assertEqual(expected2, result2)
        self.assertEqual(expected3, result3)
        self.assertNotEqual(tree, other_tree)
        self.assertNotEqual(other_tree, tree)
        self.assertEqual(tree, copy_tree)

    def test_copy(self):
        europe = self.tree["Europe"]
        shallow_copy = copy.copy(europe)
        deep_copy = copy.deepcopy(europe)

        shallow_copy._check_integrity()
        deep_copy._check_integrity()

        self.assertEqual(europe, shallow_copy)
        self.assertEqual(europe, deep_copy)

    def test_copy_depth(self):
        europe = self.tree["Europe"]
        shallow_copy = europe.copy(keep=MaxDepth(1))
        deep_copy = europe.copy(keep=MaxDepth(1), deep=True)
        europe_pruned = Node(identifier="Europe")
        europe_pruned.path.create("Norway")
        europe_pruned.path.create("Sweden")
        europe_pruned.path.create("Finland")

        europe_pruned.show()
        shallow_copy.show()
        deep_copy.show()

        shallow_copy._check_integrity()
        deep_copy._check_integrity()

        self.assertEqual(europe_pruned, shallow_copy)
        self.assertEqual(europe_pruned, deep_copy)
