from unittest import TestCase

from littletree import Node
from littletree.exceptions import DifferentTreeError
from littletree.route import Route


class TestRoute(TestCase):
    def setUp(self) -> None:
        tree = Node(identifier="world")
        tree.path.create(["Europe", "Norway", "Oslo"])
        tree.path.create(["Europe", "Sweden", "Stockholm"])
        tree.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        tree.path.create(["Africa"])
        self.tree = tree

        finland = tree.path("Europe/Finland")
        africa = tree.path("Africa")
        sweden = tree.path("Europe/Sweden")

        self.route = Route(finland, africa)
        self.route2 = Route(finland, sweden)
        self.route3 = Route(finland, africa, sweden)
        self.route4 = Route(africa, finland, sweden)
        self.route5 = Route(sweden.parent, sweden, sweden.parent, sweden)

    def test_repr(self):
        result = repr(self.route)
        self.assertEqual("Route(Finland, Africa)", result)

        result = repr(self.route2)
        self.assertEqual("Route(Finland, Sweden)", result)

        result = repr(self.route3)
        self.assertEqual("Route(Finland, Africa, Sweden)", result)

    def test_iter(self):
        tree = self.tree
        result = list(self.route)
        expected = [
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.root,
            tree["Africa"],
        ]
        self.assertEqual(expected, result)

        result = list(self.route2)
        expected = [
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

        result = list(self.route3)
        expected = [
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.root,
            tree["Africa"],
            tree.root,
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

        result = list(self.route4)
        expected = [
            tree["Africa"],
            tree.root,
            tree["Europe"],
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

        result = list(self.route5)
        expected = [
            tree["Europe"],
            tree.path("Europe/Sweden"),
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

    def test_reversed(self):
        tree = self.tree
        result = list(reversed(self.route))
        expected = [
            tree["Africa"],
            tree.root,
            tree["Europe"],
            tree.path("Europe/Finland"),
        ]
        self.assertEqual(expected, result)

    def test_lca(self):
        tree = self.tree
        result = self.route.lca()
        expected = tree.root
        self.assertEqual(expected, result)

        result = self.route2.lca()
        expected = tree["Europe"]
        self.assertEqual(expected, result)

        result = self.route3.lca()
        expected = tree.root
        self.assertEqual(expected, result)

    def test_iter_lca(self):
        result = list(self.route3.iter_lca())
        expected = [self.tree, self.tree]
        self.assertEqual(expected, result)

        result = list(self.route4.iter_lca())
        expected = [self.tree.root, self.tree.path("Europe")]
        self.assertEqual(expected, result)

    def test_len(self):
        tree = self.tree
        result = len(self.route)
        self.assertEqual(4, result)

        result = len(self.route2)
        self.assertEqual(3, result)

        result = len(self.route3)
        self.assertEqual(7, result)

        result = len(self.route4)
        self.assertEqual(6, result)

        result = len(self.route5)
        self.assertEqual(4, result)

        deep_helsinki = tree.path(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        route = Route(deep_helsinki, deep_helsinki)
        route_from_route = Route(deep_helsinki.root, deep_helsinki)
        result = len(route)
        result2 = len(deep_helsinki.path)
        result3 = len(route_from_route)
        self.assertEqual(1, result)
        self.assertEqual(6, result2)
        self.assertEqual(6, result3)

    def test_path_to_different_tree(self):
        """It's impossible to make path to a tree with a different root."""
        tree = self.tree
        other_tree = Node(identifier='disconnected')
        self.assertIsNot(tree.root, other_tree.root)

        with self.assertRaises(DifferentTreeError):
            Route(tree, other_tree, check_tree=True)
