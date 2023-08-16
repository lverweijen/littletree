from unittest import TestCase

from node import Node


class TestNode(TestCase):
    def setUp(self) -> None:
        root = Node(identifier="world")
        root.path.create("Europe", "Norway", "Oslo")
        root.path.create("Europe", "Sweden", "Stockholm")
        root.path.create("Europe", "Finland", "Helsinki", "Helsinki", "Helsinki")
        root.path.create("Africa")

        self.tree = root

    def test_item(self):
        self.tree["South-America"] = Node(identifier="old_name")
        self.assertEqual("South-America", self.tree["South-America"].identifier)

    def test_item_rename(self):
        self.tree["South-America"] = Node(identifier="old_name")
        self.tree["South-America"].identifier = "Sur-America"
        self.assertEqual("Sur-America", self.tree["Sur-America"].identifier)

        with self.assertRaises(KeyError):
            self.tree["South-America"]

        self.tree._check_integrity()

    def test_item_update_dict(self):
        self.tree.update({"Antarctica": Node()})
        self.assertEqual(self.tree["Antarctica"].identifier, "Antarctica")
        self.tree._check_integrity()

    def test_item_update_iterable(self):
        self.tree.update([Node(identifier="Antarctica")])
        self.assertEqual(self.tree["Antarctica"].identifier, "Antarctica")
        self.tree._check_integrity()

    def test_item_update_swap(self):
        # Swap Europe and Africa. This is crazy!
        self.tree["Europe"], self.tree["Africa"] = self.tree["Africa"].detach(), self.tree["Europe"].detach()
        self.assertEqual("Norway", self.tree.path("Africa", "Norway").identifier)
        self.tree._check_integrity()

    def test_iter_children(self):
        result = [str(child.path) for child in self.tree.iter_children()]
        expected = ['/world/Europe', '/world/Africa']
        self.assertEqual(expected, result)

    def test_iter_tree(self):
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

    def test_iter_tree_first(self):
        """Iterate only through nodes which are first-child."""
        def is_first_child(index, **_):
            return index == 0

        result = [str(child.path) for child in self.tree.iter_tree(is_first_child)]
        expected = [
            '/world',
            '/world/Europe',
            '/world/Europe/Norway',
            '/world/Europe/Norway/Oslo',
        ]
        self.assertEqual(expected, result)

    def test_iter_ancestors(self):
        target = self.tree.path("Europe", "Norway", "Oslo")
        result = [str(child.path) for child in target.iter_ancestors()]
        expected = ['/world/Europe/Norway', '/world/Europe', "/world"]
        self.assertEqual(expected, result)

    def test_iter_descendants(self):
        target = self.tree.path("Europe", "Finland")
        result = [str(child.path) for child in target.iter_descendants()]
        expected = [
            '/world/Europe/Finland/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki/Helsinki',
        ]
        self.assertEqual(expected, result)

    def test_iter_descendants_postorder(self):
        target = self.tree.path("Europe", "Finland")
        result = [str(child.path) for child in target.iter_descendants(post_order=True)]
        expected = [
            '/world/Europe/Finland/Helsinki/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki/Helsinki',
            '/world/Europe/Finland/Helsinki',
        ]
        self.assertEqual(expected, result)

    def test_iter_siblings(self):
        target = self.tree.path("Europe", "Finland")
        result = [str(child.path) for child in target.iter_siblings()]
        expected = ['/world/Europe/Norway', '/world/Europe/Sweden']
        self.assertEqual(expected, result)

    def test_iter_path(self):
        target = self.tree.path("Europe", "Norway", "Oslo")
        result = [str(child.path) for child in target.iter_path()]
        expected = ['/world', '/world/Europe', '/world/Europe/Norway', '/world/Europe/Norway/Oslo']
        self.assertEqual(expected, result)

    def test_iter_leaves(self):
        target = self.tree.path("Europe")
        result = [(child.identifier) for child in target.iter_leaves()]
        expected = ['Oslo', 'Stockholm', 'Helsinki']
        self.assertEqual(expected, result)
