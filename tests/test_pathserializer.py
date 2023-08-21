from unittest import TestCase

from export.rowserializer import RowSerializer
from node import Node


class TestRowSerializer(TestCase):
    def setUp(self) -> None:
        tree = Node(identifier="world")
        tree.path.create(["Europe", "Norway", "Oslo"])
        tree.path.create(["Europe", "Sweden", "Stockholm"])
        tree.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        tree.path.create(["Africa"])

        tree["Europe"].data = {"abbrev": "EU"}
        tree["Europe"]["Norway"].data = {"abbrev": "NO"}

        self.tree = tree

        self.rows = [
            {"path": ('Europe',), "data": {"abbrev": "EU"}},
            {"path": ('Europe', 'Norway'), "data": {"abbrev": "NO"}},
            {"path": ('Europe', 'Norway', 'Oslo'), "data": None},
            {"path": ('Europe', 'Sweden'), "data": None},
            {"path": ('Europe', 'Sweden', 'Stockholm'), "data": None},
            {"path": ('Europe', 'Finland'), "data": None},
            {"path": ('Europe', 'Finland', 'Helsinki'), "data": None},
            {"path": ('Europe', 'Finland', 'Helsinki', 'Helsinki'), "data": None},
            {"path": ('Europe', 'Finland', 'Helsinki', 'Helsinki', 'Helsinki'), "data": None},
            {"path": ('Africa',), "data": None},
        ]

    def test_to_rows1(self):
        """Only export path names."""
        serializer = RowSerializer(Node, path_name=None)
        result = list(serializer.to_rows(self.tree))
        expected = [row["path"] for row in self.rows]
        self.assertEqual(expected, result)

    def test_to_rows2(self):
        """Export path names in path attribute."""
        serializer = RowSerializer(Node, path_name="path")
        result = list(serializer.to_rows(self.tree))
        expected = [{"path": row["path"]} for row in self.rows]
        self.assertEqual(expected, result)

    def test_to_rows3(self):
        """Test with path name as tuple"""
        serializer = RowSerializer(Node, path_name=["Continent", "Country", "Capital"])
        result = list(serializer.to_rows(self.tree))

        expected = [
            {'Continent': 'Europe'},
            {'Continent': 'Europe', 'Country': 'Norway'},
            {'Continent': 'Europe', 'Country': 'Norway', 'Capital': 'Oslo'},
            {'Continent': 'Europe', 'Country': 'Sweden'},
            {'Continent': 'Europe', 'Country': 'Sweden', 'Capital': 'Stockholm'},
            {'Continent': 'Europe', 'Country': 'Finland'},
            {'Continent': 'Europe', 'Country': 'Finland', 'Capital': 'Helsinki'},
            {'Continent': 'Africa'}
        ]
        self.assertEqual(expected, result)

    def test_to_rows4(self):
        """Test with path name as tuple, leaves only"""
        serializer = RowSerializer(Node, path_name=["Continent", "Country", "Capital"])
        result = list(serializer.to_rows(self.tree, leaves_only=True))
        expected = [
            {'Continent': 'Europe', 'Country': 'Norway', 'Capital': 'Oslo'},
            {'Continent': 'Europe', 'Country': 'Sweden', 'Capital': 'Stockholm'},
            {'Continent': 'Africa'}
        ]
        self.assertEqual(expected, result)

    def test_to_rows5(self):
        """Test with path name as tuple, leaves only"""
        serializer = RowSerializer(Node, path_name=["Continent", "Country", "Capital"], fields=["data"])
        result = list(serializer.to_rows(self.tree))
        expected = [
            {'Continent': 'Europe', 'data': {'abbrev': 'EU'}},
            {'Continent': 'Europe', 'Country': 'Norway', 'data': {'abbrev': 'NO'}},
            {'Capital': 'Oslo', 'Continent': 'Europe', 'Country': 'Norway', 'data': None},
            {'Continent': 'Europe', 'Country': 'Sweden', 'data': None},
            {'Capital': 'Stockholm',
             'Continent': 'Europe',
             'Country': 'Sweden',
             'data': None},
            {'Continent': 'Europe', 'Country': 'Finland', 'data': None},
            {'Capital': 'Helsinki',
             'Continent': 'Europe',
             'Country': 'Finland',
             'data': None},
            {'Continent': 'Africa', 'data': None}
        ]
        self.assertEqual(expected, result)

    def test_from_rows(self):
        """Without data."""
        serializer = RowSerializer(Node, path_name=None)
        paths = [row["path"] for row in self.rows]
        result = serializer.from_rows(paths)
        result.identifier = "world"  # Set root identifier

        # We didn't have data, so delete it from expected
        expected = self.tree
        for node in expected.iter_tree():
            node.data = None

        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_rows2(self):
        """With data and path field."""
        serializer = RowSerializer(Node, path_name="path", fields=["data"])
        result = serializer.from_rows(self.rows)
        result.identifier = "world"  # Set root identifier

        expected = self.tree

        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_rows3(self):
        """With data and separate fields."""
        serializer = RowSerializer(Node, path_name=["Continent", "Country"], fields=["data"])
        rows = [
            {'Continent': 'Europe', 'Country': 'Norway', "data": {"Capital": 'Oslo'}},
            {'Continent': 'Europe', 'Country': 'Sweden', "data": {"Capital": 'Stockholm'}},
            {'Continent': 'Africa', "data": None}
        ]
        result = serializer.from_rows(rows)
        result.identifier = "world"  # Set root identifier

        # We didn't have data, so delete it from expected
        expected = {'data': None,
                    'children': {'Africa': {'data': None},
                                 'Europe': {'data': None,
                                            'children': {'Norway': {"data": {'Capital': "Oslo"}},
                                                         'Sweden': {"data": {'Capital': "Stockholm"}}}}} }

        self.assertEqual(expected, result.to_dict())
