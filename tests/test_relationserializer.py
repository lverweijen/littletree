import copy
from unittest import TestCase

from littletree import Node
from littletree.serializers import RelationSerializer


class TestRowSerializer(TestCase):
    def setUp(self) -> None:
        tree = Node(identifier="world")
        tree.path.create(["Europe", "Norway", "Oslo"])
        tree.path.create(["Europe", "Sweden", "Stockholm"])
        tree.path.create(["Europe", "Finland", "Helsinki"])
        tree.path.create(["Africa"])
        
        tree2 = tree.copy()
        tree2["Europe"].data = {"abbrev": "EU"}
        tree2["Europe"]["Norway"].data = {"abbrev": "NO"}

        self.tree = tree
        self.tree2 = tree2

        self.relations = [
            {'identifier': 'Europe', 'parent': 'world'},
            {'identifier': 'Norway', 'parent': 'Europe'},
            {'identifier': 'Oslo', 'parent': 'Norway'},
            {'identifier': 'Sweden', 'parent': 'Europe'},
            {'identifier': 'Stockholm', 'parent': 'Sweden'},
            {'identifier': 'Finland', 'parent': 'Europe'},
            {'identifier': 'Helsinki', 'parent': 'Finland'},
            {'identifier': 'Africa', 'parent': 'world'},
        ]

        self.relations2 = copy.deepcopy(self.relations)
        for row in self.relations2:
            row["data"] = None
            if row["identifier"] == "Europe":
                row["data"] = {'abbrev': 'EU'}
            elif row["identifier"] == "Norway":
                row["data"] = {'abbrev': 'NO'}
            else:
                row["data"] = {}

        self.relations3 = copy.deepcopy(self.relations)
        for row in self.relations3:
            if row["identifier"] == "Europe":
                row["abbrev"] = "EU"
            elif row["identifier"] == "Norway":
                row["abbrev"] = "NO"

    def test_to_relations(self):
        """Only export child/parent."""
        serializer = RelationSerializer(Node)
        result = list(serializer.to_relations(self.tree))
        expected = self.relations
        self.assertEqual(expected, result)

    def test_to_relations2(self):
        """With data."""
        serializer = RelationSerializer(Node, fields=("data",))
        result = list(serializer.to_relations(self.tree2))
        expected = self.relations2
        self.assertEqual(expected, result)

    def test_to_relations3(self):
        """With data."""
        serializer = RelationSerializer(Node, data_field="data")
        result = list(serializer.to_relations(self.tree2))
        expected = self.relations3
        self.assertEqual(expected, result)

    def test_from_relations(self):
        """Without data."""
        serializer = RelationSerializer(Node)
        result = serializer.from_relations(self.relations)

        # We didn't supply a root, so the tree has one extra level of nesting, remove it first
        result = result['world'].detach()

        # We didn't have data, so delete it from expected
        expected = self.tree

        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_relations2(self):
        """Without data."""
        serializer = RelationSerializer(Node, fields=["data"])
        result = serializer.from_relations(self.relations2)

        # We didn't supply a root, so the tree has one extra level of nesting, remove it first
        result = result['world'].detach()

        # We didn't have data, so delete it from expected
        expected = self.tree2
        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_relations2(self):
        """Without data."""
        serializer = RelationSerializer(Node, fields=["data"])
        result = serializer.from_relations(self.relations2)

        # We didn't supply a root, so the tree has one extra level of nesting, remove it first
        result = result['world'].detach()

        # We didn't have data, so delete it from expected
        expected = self.tree2
        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_relations3(self):
        """Without data."""
        serializer = RelationSerializer(Node, data_field="data")
        result = serializer.from_relations(self.relations3)

        # We didn't supply a root, so the tree has one extra level of nesting, remove it first
        result = result['world'].detach()

        # We didn't have data, so delete it from expected
        expected = self.tree2
        self.assertEqual(expected.to_dict(), result.to_dict())

    def test_from_df(self):
        """Without data."""
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("Pandas not installed")
            return

        df = pd.DataFrame([
            {"identifier": "Stockholm", "parent": "Sweden"},
            {"identifier": "Hagfors", "parent": "Sweden"},
            {"identifier": "Sweden", "parent": "Europe"},
        ])

        serializer = RelationSerializer(Node)
        result = serializer.from_relations(df, root="Europe")

        # We didn't have data, so delete it from expected
        expected = Node(
            identifier="Europe",
            children={
                "Sweden": Node(children={
                    "Stockholm": Node(),
                    "Hagfors": Node(),
                })
            })

        self.assertEqual(expected, result)
