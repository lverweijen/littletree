from unittest import TestCase

from littletree import Node


class TestPath(TestCase):
    def setUp(self) -> None:
        tree = Node(identifier="world")
        tree.path.create(["Europe", "Norway", "Oslo"])
        tree.path.create(["Europe", "Sweden", "Stockholm"])
        tree.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        tree.path.create(["Africa"])

        self.tree = tree

    def test_eq(self):
        self.assertEqual(self.tree.path, self.tree.path)
        self.assertEqual(self.tree.path, self.tree.copy().path)
        self.assertNotEqual(self.tree.path, self.tree["Europe"].path)
