from unittest import TestCase

from export.pathserializer import PathSerializer
from node import Node


class TestPathSerializer(TestCase):
    def setUp(self) -> None:
        root = Node(identifier="world")
        root.path.create(["Europe", "Norway", "Oslo"])
        root.path.create(["Europe", "Sweden", "Stockholm"])
        root.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        root.path.create(["Africa"])

        self.tree = root

        self.paths = [
            ('Europe',),
            ('Europe', 'Norway'),
            ('Europe', 'Norway', 'Oslo'),
            ('Europe', 'Sweden'),
            ('Europe', 'Sweden', 'Stockholm'),
            ('Europe', 'Finland'),
            ('Europe', 'Finland', 'Helsinki'),
            ('Europe', 'Finland', 'Helsinki', 'Helsinki'),
            ('Europe', 'Finland', 'Helsinki', 'Helsinki', 'Helsinki'),
            ('Africa',)]

    def test_to_path1(self):
        """Test with path name str"""
        serializer = PathSerializer(Node, path_name=None)
        result = list(serializer.to_path(self.tree))
        expected = self.paths
        self.assertEqual(expected, result)

    def test_to_path2(self):
        """Test with path name None"""
        serializer = PathSerializer(Node)
        result = list(serializer.to_path(self.tree))
        expected = [{"path": path} for path in self.paths]
        self.assertEqual(expected, result)

    def test_to_path3(self):
        """Test with path name as tuple"""
        serializer = PathSerializer(Node, path_name=["Continent", "Country", "Capital"])
        result = list(serializer.to_path(self.tree))

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

    def test_to_path4(self):
        """Test with path name as tuple, leaves only"""
        serializer = PathSerializer(Node, path_name=["Continent", "Country", "Capital"])
        result = list(serializer.to_path(self.tree, leaves_only=True))
        expected = [
            {'Continent': 'Europe', 'Country': 'Norway', 'Capital': 'Oslo'},
            {'Continent': 'Europe', 'Country': 'Sweden', 'Capital': 'Stockholm'},
            {'Continent': 'Africa'}
        ]
        self.assertEqual(expected, result)

    def test_from_path(self):
        serializer = PathSerializer(Node, path_name=None)
        result = serializer.from_path(self.paths)
        expected = self.tree
        self.assertEqual(expected.to_dict(), result.to_dict())
