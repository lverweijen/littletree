from unittest import TestCase, skip

import littletree


class TestRecursive(TestCase):
    def setUp(self) -> None:
        # Set up a very difficult problem on which recursion is likely to fail
        node = littletree.Node()
        node.path.create(range(8000))
        node.path([0, 1]).update([littletree.Node(identifier=10 + i) for i in range(8000)])
        self.node = node

    def test_recursion1(self):
        for repeat in range(100):
            list(self.node.iter_tree(order='pre'))

    def test_recursion2(self):
        for repeat in range(100):
            list(self.node.iter_tree(order='post'))

    def test_recursion3(self):
        for repeat in range(100):
            list(self.node.iter_tree(order='level'))

    def test_copy(self):
        for repeat in range(10):
            self.node.copy()

    def test_deepcopy(self):
        for repeat in range(10):
            self.node.deepcopy()

    @skip("too difficult")
    def test_to_rows(self):
        for repeat in range(10):
            list(self.node.to_rows())

    @skip("too difficult")
    def test_to_dict(self):
        self.node.to_dict()

    def test_to_string(self):
        self.node.to_string()
