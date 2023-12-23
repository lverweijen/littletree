from unittest import TestCase

from littletree import Node


class TestNode(TestCase):
    def setUp(self) -> None:
        tree = Node(identifier="world")
        tree.path.create(["Europe", "Norway", "Oslo"])
        tree.path.create(["Europe", "Sweden", "Stockholm"])
        tree.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        tree.path.create(["Africa"])

        self.tree = tree

    def test_str(self):
        tree = self.tree
        result = str(tree.path("Europe/Finland").path.to(tree["Africa"]))
        self.assertEqual("../../Africa", result)

        result = str(tree.path("Europe/Finland").path.to(tree.path("Europe/Sweden")))
        self.assertEqual("../Sweden", result)

    def test_eq(self):
        self.assertEqual(self.tree.path, self.tree.path)
        self.assertEqual(self.tree.path, self.tree.copy().path)
        self.assertNotEqual(self.tree.path, self.tree["Europe"].path)

    def test_iter(self):
        tree = self.tree
        result = list(tree.path("Europe/Finland").path.to(tree["Africa"]))
        expected = [
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.root,
            tree["Africa"],
        ]
        print("expected = {!r}".format(expected))
        self.assertEqual(expected, result)

        result = list(tree.path("Europe/Finland").path.to(tree.path("Europe/Sweden")))
        expected = [
            tree.path("Europe/Finland"),
            tree["Europe"],
            tree.path("Europe/Sweden"),
        ]
        self.assertEqual(expected, result)

    def test_reversed(self):
        tree = self.tree
        result = list(reversed(tree.path("Europe/Finland").path.to(tree["Africa"])))
        expected = [
            tree["Africa"],
            tree.root,
            tree["Europe"],
            tree.path("Europe/Finland"),
        ]
        self.assertEqual(expected, result)

    def test_lca(self):
        tree = self.tree
        result = tree.path("Europe/Finland").path.to(tree["Africa"]).lca
        expected = tree.root
        self.assertEqual(expected, result)

        result = tree.path("Europe/Finland").path.to(tree.path("Europe/Sweden")).lca
        expected = tree["Europe"]
        self.assertEqual(expected, result)

    def test_to_len(self):
        tree = self.tree
        result = len(tree.path("Europe/Finland").path.to(tree["Africa"]))
        self.assertEqual(4, result)

        result = len(tree.path("Europe/Finland").path.to(tree.path("Europe/Sweden")))
        self.assertEqual(3, result)

        deep_helsinki = tree.path(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        result = len(deep_helsinki.root.path.to(deep_helsinki))
        result2 = len(deep_helsinki.path)
        self.assertEqual(6, result)
        self.assertEqual(6, result2)

    def test_path_to_different_tree(self):
        """It's impossible to make path to a tree with a different root."""
        tree = self.tree
        other_tree = Node(identifier='disconnected')
        self.assertIsNot(tree.root, other_tree.root)
        self.assertIsNone(tree.path.to(other_tree))
