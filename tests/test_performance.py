from unittest import TestCase

import littletree
from littletree import Node

"""
This is used to check that certain operations that should be fast
aren't accidentally slow.
"""


class TestPerformance(TestCase):
    def setUp(self) -> None:
        # Set up a reasonably difficult problem on which recursion is likely to fail
        # Not too difficult, because we want the test to run quickly
        tree = littletree.Node()
        tree.path.create(range(800))
        tree.path([0, 1]).update([littletree.Node(identifier=10 + i) for i in range(800)])
        self.tree = tree
        self.s = tree.to_newick()

    def test_recursion1(self):
        nodes = self.tree.nodes
        for repeat in range(100):
            list(nodes.preorder())

    def test_recursion2(self):
        nodes = self.tree.nodes
        for repeat in range(100):
            list(nodes.postorder())

    def test_recursion3(self):
        nodes = self.tree.nodes
        for repeat in range(100):
            list(nodes.levelorder())

    def test_equal(self):
        copy = self.tree.copy()
        for repeat in range(100):
            self.tree == copy

    def test_copy(self):
        for repeat in range(10):
            self.tree.copy()

    def test_deepcopy(self):
        for repeat in range(10):
            self.tree.copy({})

    def test_to_rows(self):
        for repeat in range(10):
            list(self.tree.to_rows(sep=None))

    def test_to_relations(self):
        for repeat in range(100):
            list(self.tree.to_relations())

    def test_to_dict(self):
        for i in range(100):
            self.tree.to_dict()

    def test_to_string(self):
        self.tree.to_string()

    def test_to_newick(self):
        for i in range(100):
            self.tree.to_newick(dialect="newick")

    def test_from_newick(self):
        s = self.s
        for i in range(10):
            Node.from_newick(s, dialect="newick")
