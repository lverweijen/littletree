from unittest import TestCase

from littletree import Node
from littletree.serializers import DictSerializer


class TestDictSerializer(TestCase):
    def setUp(self) -> None:
        root = Node(identifier="world")
        root.path.create(["Europe", "Norway", "Oslo"])
        root.path.create(["Europe", "Sweden", "Stockholm"])
        root.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        root.path.create(["Africa"])

        self.tree = root
        self.compact_dict = {'Africa': {},
                             'Europe': {'Finland': {'Helsinki': {'Helsinki': {'Helsinki': {}}}},
                                        'Norway': {'Oslo': {}},
                                        'Sweden': {'Stockholm': {}}}}
        self.verbose_dict = {
            'name': 'world',
            'children': [{'name': 'Europe',
                          'children': [
                              {'name': 'Norway',
                               'children': [{'name': 'Oslo'}]},
                              {'name': 'Sweden',
                               'children': [{'name': 'Stockholm'}]},
                              {'name': 'Finland',
                               'children': [{'name': 'Helsinki',
                                             'children': [
                                                 {'name': 'Helsinki',
                                                  'children': [{'name': 'Helsinki'}]}]}]}]},
                         {'name': 'Africa'}]
        }

    def test_to_dict_error(self):
        node = Node('data')
        try:
            node.to_dict()
        except ValueError as e:
            self.assertEqual("data might not be a dictionary. "
                             "Consider node.to_dict(fields=['data']) instead.", str(e))
        else:
            self.fail("Exception was expected")

    def test_to_dict1(self):
        """Compact serialization.

        Note that identifier "world" is lost from output.
        """
        serializer = DictSerializer(Node, children_name=None)
        result = serializer.to_dict(self.tree)
        expected = self.compact_dict
        self.assertEqual(expected, result)

    def test_to_dict2(self):
        """Verbose but extensible serialization."""
        serializer = DictSerializer(Node, node_name="name", children_name="children")
        result = serializer.to_dict(self.tree)
        expected = self.verbose_dict
        self.assertEqual(expected, result)

    def test_from_dict1(self):
        serializer = DictSerializer(Node, children_name=None)
        result = serializer.from_dict(self.compact_dict)
        result.identifier = "world"  # Needs to be updated by hand
        expected = self.tree
        result._check_integrity()
        self.assertEqual(len(expected.children), len(result.children))

    def test_from_dict2(self):
        """Verbose but extensible serialization."""

        serializer = DictSerializer(Node, node_name="name", children_name="children")
        result = serializer.from_dict(self.verbose_dict)
        expected = self.tree
        result._check_integrity()
        self.assertEqual(len(expected.children), len(result.children))
