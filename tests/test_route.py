from unittest import TestCase

from littletree import Node


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

        self.route = finland.to(africa)
        self.route2 = finland.to(sweden)
        self.route3 = finland.to(africa, sweden)
        self.route4 = africa.to(finland, sweden)
        self.route5 = sweden.parent.to(sweden, sweden.parent, sweden)

    def test_repr(self):
        result = repr(self.route)
        self.assertEqual("Route(Finland, Africa)", result)

        result = repr(self.route2)
        self.assertEqual("Route(Finland, Sweden)", result)

        result = repr(self.route3)
        self.assertEqual("Route(Finland, Africa, Sweden)", result)

    def test_iter(self):
        tree = self.tree
        result = list(self.route.nodes)
        expected = [
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.root,
            tree["Africa"],
        ]
        self.assertEqual(expected, result)

        result = list(self.route2.nodes)
        expected = [
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

        result = list(self.route3.nodes)
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

        result = list(self.route4.nodes)
        expected = [
            tree["Africa"],
            tree.root,
            tree["Europe"],
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

        result = list(self.route5.nodes)
        expected = [
            tree["Europe"],
            tree.path("Europe/Sweden"),
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

    def test_reversed(self):
        tree = self.tree
        result = list(reversed(list(self.route.nodes)))
        expected = [
            tree["Africa"],
            tree.root,
            tree["Europe"],
            tree.path("Europe/Finland"),
        ]
        self.assertEqual(expected, result)

    def test_lca(self):
        tree = self.tree
        result = self.route.lca
        expected = tree.root
        self.assertIs(expected, result)

        result = self.route2.lca
        expected = tree["Europe"]
        self.assertIs(expected, result)

        result = self.route3.lca
        expected = tree.root
        self.assertIs(expected, result)

    def test_count_nodes(self):
        tree = self.tree
        result = self.route.nodes.count()
        self.assertEqual(4, result)

        result = self.route2.nodes.count()
        self.assertEqual(3, result)

        result = self.route3.nodes.count()
        self.assertEqual(7, result)

        result = self.route4.nodes.count()
        self.assertEqual(6, result)

        result = self.route5.nodes.count()
        self.assertEqual(4, result)

        deep_helsinki = tree.path(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        route = deep_helsinki.to(deep_helsinki)
        route_from_route = deep_helsinki.root.to(deep_helsinki)
        result = route.nodes.count()
        result2 = deep_helsinki.path.count()
        result3 = route_from_route.nodes.count()
        self.assertEqual(1, result)
        self.assertEqual(6, result2)
        self.assertEqual(6, result3)

    def test_path_to_different_tree(self):
        """It's impossible to make path to a tree with a different root."""
        tree = self.tree
        other_tree = Node(identifier='disconnected')
        self.assertIsNot(tree.root, other_tree.root)
        self.assertIsNone(tree.to(other_tree))
