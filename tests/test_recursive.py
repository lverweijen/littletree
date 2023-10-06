from unittest import TestCase, skip

import littletree
from littletree import Node


class TestRecursive(TestCase):
    def setUp(self) -> None:
        # Set up a very difficult problem on which recursion is likely to fail
        node = littletree.Node()
        node.path.create(range(800))
        node.path([0, 1]).update([littletree.Node(identifier=10 + i) for i in range(800)])
        self.node = node
        self.s = node.to_newick()

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
            self.node.copy({})

    def test_to_rows(self):
        for repeat in range(10):
            list(self.node.to_rows(sep=None))

    def test_to_relations(self):
        for repeat in range(100):
            list(self.node.to_relations())

    def test_to_dict(self):
        for i in range(100):
            self.node.to_dict()

    def test_to_string(self):
        self.node.to_string()

    def test_to_newick(self):
        for i in range(100):
            self.node.to_newick(dialect="newick")

    def test_from_newick(self):
        s = self.s
        for i in range(10):
            Node.from_newick(s, dialect="newick")
