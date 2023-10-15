from unittest import TestCase

from littletree import Node
from littletree.serializers import RowSerializer
from littletree.serializers.rowserializer import RowSerializerError


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
            {"path": ('Europe', 'Norway', 'Oslo'), "data": {}},
            {"path": ('Europe', 'Sweden'), "data": {}},
            {"path": ('Europe', 'Sweden', 'Stockholm'), "data": {}},
            {"path": ('Europe', 'Finland'), "data": {}},
            {"path": ('Europe', 'Finland', 'Helsinki'), "data": {}},
            {"path": ('Europe', 'Finland', 'Helsinki', 'Helsinki'), "data": {}},
            {"path": ('Europe', 'Finland', 'Helsinki', 'Helsinki', 'Helsinki'), "data": {}},
            {"path": ('Africa',), "data": {}},
        ]

    def test_to_rows1(self):
        """Only export path names."""
        serializer = RowSerializer(Node, path_name=None)
        result = list(serializer.to_rows(self.tree))
        expected = [row["path"] for row in self.rows]
        self.assertEqual(expected, result)

    def test_to_rows2(self):
        """Export path names in path attribute."""
        serializer = RowSerializer(Node, path_name="path", sep=None)
        result = list(serializer.to_rows(self.tree))
        expected = [{"path": row["path"]} for row in self.rows]
        self.assertEqual(expected, result)

    def test_to_rows3a(self):
        """Test with path name as tuple"""
        path_name = ["Continent", "Country", "Capital"]
        serializer = RowSerializer(Node, path_name, sep=None)

        with self.assertRaises(RowSerializerError):
            list(serializer.to_rows(self.tree))

    def test_to_rows3b(self):
        """Test with path name as tuple"""
        path_name = ["Continent", "Country", "Capital", "Subcaptital", "Subsubcapital"]
        serializer = RowSerializer(Node, path_name, sep=None)
        result = list(serializer.to_rows(self.tree))

        expected = [
            {'Continent': 'Europe'},
            {'Continent': 'Europe', 'Country': 'Norway'},
            {'Continent': 'Europe', 'Country': 'Norway', 'Capital': 'Oslo'},
            {'Continent': 'Europe', 'Country': 'Sweden'},
            {'Continent': 'Europe', 'Country': 'Sweden', 'Capital': 'Stockholm'},
            {'Continent': 'Europe', 'Country': 'Finland'},
            {'Continent': 'Europe', 'Country': 'Finland', 'Capital': 'Helsinki'},
            {'Capital': 'Helsinki', 'Continent': 'Europe', 'Country': 'Finland',
             'Subcaptital': 'Helsinki'},
            {'Capital': 'Helsinki', 'Continent': 'Europe', 'Country': 'Finland',
             'Subcaptital': 'Helsinki', 'Subsubcapital': 'Helsinki'},
            {'Continent': 'Africa'}
        ]
        self.assertEqual(expected, result)

    def test_to_rows4(self):
        """Test with path name as tuple, leaves only"""
        path_name = ["Continent", "Country", "Capital", "Subcaptital", "Subsubcapital"]
        serializer = RowSerializer(Node, path_name=path_name, sep=None)
        result = list(serializer.to_rows(self.tree, leaves_only=True))
        expected = [
            {'Continent': 'Europe', 'Country': 'Norway', 'Capital': 'Oslo'},
            {'Continent': 'Europe', 'Country': 'Sweden', 'Capital': 'Stockholm'},
            {'Capital': 'Helsinki',
             'Continent': 'Europe',
             'Country': 'Finland',
             'Subcaptital': 'Helsinki',
             'Subsubcapital': 'Helsinki'},
            {'Continent': 'Africa'}
        ]
        self.assertEqual(expected, result)

    def test_to_rows5(self):
        """Test with path name as tuple, leaves only, test with data"""
        path_name = ["Continent", "Country", "Capital", "Subcaptital", "Subsubcapital"]
        serializer = RowSerializer(Node, path_name=path_name, fields=["data"], sep=None)
        result = list(serializer.to_rows(self.tree))
        expected = [
            {'Continent': 'Europe', 'data': {'abbrev': 'EU'}},
            {'Continent': 'Europe', 'Country': 'Norway', 'data': {'abbrev': 'NO'}},
            {'Capital': 'Oslo', 'Continent': 'Europe', 'Country': 'Norway', 'data': {}},
            {'Continent': 'Europe', 'Country': 'Sweden', 'data': {}},
            {'Capital': 'Stockholm',
             'Continent': 'Europe',
             'Country': 'Sweden',
             'data': {}},
            {'Continent': 'Europe', 'Country': 'Finland', 'data': {}},
            {'Capital': 'Helsinki',
             'Continent': 'Europe',
             'Country': 'Finland',
             'data': {}},
            {'Capital': 'Helsinki',
             'Continent': 'Europe',
             'Country': 'Finland',
             'Subcaptital': 'Helsinki',
             'data': {}},
            {'Capital': 'Helsinki',
             'Continent': 'Europe',
             'Country': 'Finland',
             'Subcaptital': 'Helsinki',
             'Subsubcapital': 'Helsinki',
             'data': {}},
            {'Continent': 'Africa', 'data': {}}
        ]
        self.assertEqual(expected, result)

    def test_to_rows6(self):
        """Test with path name as tuple, leaves only"""
        path_name = ["Country", "Capital", "Subcaptital", "Subsubcapital"]
        serializer = RowSerializer(Node, path_name=path_name, data_field="data", sep=None,)
        result = list(serializer.to_rows(self.tree.path("Europe/Finland"), with_root=True))
        expected = [
            {'Country': 'Finland'},
            {'Country': 'Finland', 'Capital': 'Helsinki'},
            {'Country': 'Finland', 'Capital': 'Helsinki', 'Subcaptital': 'Helsinki'},
            {'Country': 'Finland', 'Capital': 'Helsinki',
             'Subcaptital': 'Helsinki', 'Subsubcapital': 'Helsinki'}
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
            node.data = {}

        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_rows2(self):
        """With data and path field."""
        serializer = RowSerializer(Node, path_name="path", fields=["data"], sep=None)
        result = serializer.from_rows(self.rows)
        result.identifier = "world"  # Set root identifier

        expected = self.tree

        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_rows3(self):
        """With data and separate fields."""
        serializer = RowSerializer(Node, path_name=["Continent", "Country"], fields=["data"], sep=None)
        rows = [
            {'Continent': 'Europe', 'Country': 'Norway', "data": {"Capital": 'Oslo'}},
            {'Continent': 'Europe', 'Country': 'Sweden', "data": {"Capital": 'Stockholm'}},
            {'Continent': 'Africa', "data": {}}
        ]
        result = serializer.from_rows(rows)
        result.identifier = "world"  # Set root identifier

        # We didn't have data, so delete it from expected
        expected = {'children': {'Africa': {},
                                 'Europe': {'children': {'Norway': {'Capital': 'Oslo'},
                                                         'Sweden': {'Capital': 'Stockholm'}}}}}

        self.assertEqual(expected, result.to_dict(identifier_name=None))

    def test_from_df(self):
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("Pandas not installed")
            return

        serializer = RowSerializer(Node, path_name=None)
        paths = pd.DataFrame([row["path"] for row in self.rows])
        paths = paths.iloc[:, :2]
        result = serializer.from_rows(paths)
        result.identifier = "world"  # Set root identifier

        # Pandas would always have the same depth on every sibling
        expected = {'children': {'Africa': {'children': {None: {}}},
                                 'Europe': {'children': {None: {},
                                                         'Finland': {},
                                                         'Norway': {},
                                                         'Sweden': {}}}}}
        self.assertEqual(expected, result.to_dict(identifier_name=None))

    def test_from_df2(self):
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("Pandas not installed")
            return

        serializer = RowSerializer(Node, path_name=["Continent", "Country"], fields=["data"])
        rows = pd.DataFrame([
            {'Continent': 'Europe', 'Country': 'Norway', "data": {"Capital": 'Oslo'}},
            {'Continent': 'Europe', 'Country': 'Sweden', "data": {"Capital": 'Stockholm'}},
            {'Continent': 'Africa', "data": {}}
        ])
        result = serializer.from_rows(rows)
        result.identifier = "world"  # Set root identifier

        for node in result.iter_tree():
            if pd.isna(node.identifier):
                node.identifier = "<empty>"

        # Same depth everywhere
        expected = {'children': {'Africa': {'children': {'<empty>': {}}},
                                 'Europe': {'children': {'Norway': {'Capital': 'Oslo'},
                                                         'Sweden': {'Capital': 'Stockholm'}}}}}

        self.assertEqual(expected, result.to_dict(identifier_name=None))
