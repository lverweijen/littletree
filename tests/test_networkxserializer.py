import unittest

from littletree import Node
from littletree.serializers import NetworkXSerializer


class TestNetworkXSerializer(unittest.TestCase):
    def test_networkx_roundtrip(self):
        """Test straight conversion to a networkx-graph and back."""
        serializer = NetworkXSerializer(data_field="data")
        tree = Node.from_newick("A(b, c, d)")
        tree['b'].data = {"corazon": "♡"}

        # Forth
        graph = serializer.to_networkx(tree)
        self.assertEqual(list("Abcd"), list(graph.nodes))
        self.assertEqual([('A', 'b'), ('A', 'c'), ('A', 'd')], list(graph.edges))
        data = dict(graph.nodes.data())

        # Check data
        self.assertEqual({}, data['A'])
        self.assertEqual({'corazon': "♡"}, data['b'])

        # Back
        tree2 = serializer.from_networkx(graph)
        self.assertIsNone(tree.compare(tree2))

    def test_networkx_roundtrip2(self):
        """Same as test_networkx_roundtrip using shortcuts."""
        tree = Node.from_newick("A(b, c, d)")
        tree['b'].data = {"corazon": 9}

        # Forth
        graph = tree.to_networkx()
        self.assertEqual(list("Abcd"), list(graph.nodes))
        self.assertEqual([('A', 'b'), ('A', 'c'), ('A', 'd')], list(graph.edges))

        # Back
        tree2 = Node.from_networkx(graph)
        self.assertIsNone(tree.compare(tree2))


if __name__ == '__main__':
    unittest.main()
