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

    def test_call(self):
        norway = self.tree.path("Europe/Norway")
        self.assertEqual(self.tree["Europe"]["Norway"], norway)

    def test_call_keyerror(self):
        with self.assertRaises(KeyError):
            self.tree.path("Europe/NorwayX")

        with self.assertRaises(KeyError):
            self.tree.path("EuropeX/Norway")

        with self.assertRaises(KeyError):
            self.tree.path("Europe/Norway/NonExistent")

    def test_get(self):
        norway = self.tree.path.get("Europe/Norway")
        fail1 = self.tree.path.get("Europe/NorwayX")
        fail2 = self.tree.path.get("EuropeX/Norway")
        fail3 = self.tree.path.get("Europe/Norway/NonExistent")

        self.assertEqual(self.tree["Europe"]["Norway"], norway)
        self.assertIsNone(fail1)
        self.assertIsNone(fail2)
        self.assertIsNone(fail3)

    def test_eq(self):
        self.assertEqual(self.tree.path, self.tree.path)
        self.assertEqual(self.tree.path, self.tree.copy().path)
        self.assertNotEqual(self.tree.path, self.tree["Europe"].path)
