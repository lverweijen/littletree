from unittest import TestCase

from littletree import Node
from littletree.serializers import DictSerializer


class TestDictSerializer(TestCase):
    def setUp(self) -> None:
        tree = Node(identifier="world")
        tree.path.create(["Europe", "Norway", "Oslo"])
        tree.path.create(["Europe", "Sweden", "Stockholm"])
        tree.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        tree.path.create(["Africa"])

        tree2 = tree.copy({})
        tree2["Europe"].data = {"abbrev": "EU"}
        tree2.path("Europe/Sweden").data = {"abbrev": "SWE"}

        self.tree, self.tree2 = tree, tree2
        self.compact_dict = {'Africa': {},
                             'Europe': {'Finland': {'Helsinki': {'Helsinki': {'Helsinki': {}}}},
                                        'Norway': {'Oslo': {}},
                                        'Sweden': {'Stockholm': {}}}}

        self.compact_data_dict = {
            'children': {'Africa': {},
                         'Europe': {'abbrev': 'EU',
                                    'children': {'Finland': {'children': {'Helsinki': {
                                        'children': {'Helsinki': {'children': {'Helsinki': {}}}}}}},
                                        'Norway': {'children': {'Oslo': {}}},
                                        'Sweden': {'abbrev': 'SWE',
                                                   'children': {'Stockholm': {}}}}}}}

        self.verbose_dict = {
            'name': 'world',
            'children': [{'name': 'Europe',
                          'abbrev': "EU",
                          'children': [
                              {'name': 'Norway',
                               'children': [{'name': 'Oslo'}]},
                              {'name': 'Sweden',
                               'abbrev': "SWE",
                               'children': [{'name': 'Stockholm'}]},
                              {'name': 'Finland',
                               'children': [{'name': 'Helsinki',
                                             'children': [
                                                 {'name': 'Helsinki',
                                                  'children': [{'name': 'Helsinki'}]}]}]}]},
                         {'name': 'Africa'}]
        }

        self.verbose_data_dict = {
            'name': 'world',
            'data': {},
            'children': [{'name': 'Europe',
                          'data': {'abbrev': "EU"},
                          'children': [
                              {'name': 'Norway',
                               'data': {},
                               'children': [{'name': 'Oslo', 'data': {}}]},
                              {'name': 'Sweden',
                               'data': {'abbrev': "SWE"},
                               'children': [{'name': 'Stockholm', 'data': {}}]},
                              {'name': 'Finland',
                               'data': {},
                               'children': [{'name': 'Helsinki',
                                             'data': {},
                                             'children': [
                                                 {'name': 'Helsinki',
                                                  'data': {},
                                                  'children': [{'name': 'Helsinki', 'data': {}}]}]}]}]},
                         {'name': 'Africa', 'data': {}}]
        }

    def test_to_dict_error(self):
        node = Node('data')
        node['child'] = Node()
        try:
            node.to_dict()
        except ValueError:
            pass  # Maybe try making this error nicer sometime
            # self.assertEqual("data might not be a dictionary. "
            #                  "Consider node.to_dict(fields=['data']) instead.", str(e))
        else:
            self.fail("Exception was expected")

    def test_to_dict1(self):
        """Compact serialization.

        Note that identifier "world" is lost from output.
        """
        serializer = DictSerializer(Node, identifier_name=None, children_name=None)
        result = serializer.to_dict(self.tree)
        expected = self.compact_dict
        self.assertEqual(expected, result)

    def test_to_dict2(self):
        """Verbose but extensible serialization."""
        serializer = DictSerializer(Node, identifier_name="name", children_name="children", data_field="data")
        result = serializer.to_dict(self.tree2)
        expected = self.verbose_dict
        self.assertEqual(expected, result)

    def test_to_dict3(self):
        """Verbose but extensible serialization."""
        serializer = DictSerializer(Node, identifier_name="name", children_name="children", fields=["data"])
        result = serializer.to_dict(self.tree2)
        expected = self.verbose_data_dict
        self.assertEqual(expected, result)

    def test_to_dict4(self):
        """Compact but extensible serialization."""
        serializer = DictSerializer(Node, identifier_name=None, children_name="children", data_field="data")
        result = serializer.to_dict(self.tree2)
        expected = self.compact_data_dict
        self.assertEqual(expected, result)

    def test_from_dict1(self):
        serializer = DictSerializer(Node, identifier_name=None, children_name=None)
        result = serializer.from_dict(self.compact_dict)
        result.identifier = "world"  # Needs to be updated by hand
        expected = self.tree
        self.assertIsNone(expected.compare(result))

    def test_from_dict2(self):
        """Verbose but extensible serialization."""

        serializer = DictSerializer(Node, identifier_name="name", children_name="children")
        result = serializer.from_dict(self.verbose_dict)
        expected = self.tree
        result._check_integrity()
        self.assertIsNone(expected.compare(result))

    def test_from_dict3(self):
        """Verbose but extensible serialization."""

        serializer = DictSerializer(Node, identifier_name="name", children_name="children", fields=["data"])
        result = serializer.from_dict(self.verbose_data_dict)
        expected = self.tree2
        result._check_integrity()
        self.assertIsNone(expected.compare(result))

    def test_from_dict4(self):
        """Verbose but extensible serialization."""

        serializer = DictSerializer(Node, identifier_name=None, children_name="children", data_field="data")
        result = serializer.from_dict(self.compact_data_dict)
        result.identifier = 'world'
        expected = self.tree2
        result._check_integrity()
        self.assertIsNone(expected.compare(result))
