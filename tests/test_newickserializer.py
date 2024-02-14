import ast
import re
from unittest import TestCase
from unittest.util import safe_repr

from littletree import Node
from littletree.serializers.newickserializer import NewickSerializer, NewickError


class TestNewickSerializer(TestCase):
    def setUp(self) -> None:
        tree = Node(identifier="world")
        tree.path.create(["Europe", "Norway", "Oslo"])
        tree.path.create(["Europe", "Sweden", "Stockholm"])
        tree.path.create(["Europe", "Finland", "Helsinki", "Helsinki", "Helsinki"])
        tree.path.create(["Africa"])

        tree2 = tree.copy()
        tree2["Europe"].data = {"abbrev": "EU"}
        tree2["Europe"]["Norway"].data = {"abbrev": "NO"}

        tree3 = tree.copy()
        tree3.data = {'distance': 0.0}  # distance on root is kinda weird, but whatever
        tree3["Europe"].data = {"distance": 5.0}
        tree3["Africa"].data = {"distance": 1.0}
        tree3["Europe"]["Norway"].data = {"distance": 1.2345}

        self.tree, self.tree2, self.tree3 = tree, tree2, tree3

    def test_to_newick1(self):
        serializer = NewickSerializer()
        result = serializer.dumps(self.tree)
        expected = ("((('Oslo')'Norway',"
                    "('Stockholm')'Sweden',"
                    "((('Helsinki')'Helsinki')'Helsinki')'Finland')'Europe','Africa')'world';")
        self.assertEqual(expected, result)

        back_tree = serializer.loads(expected)
        self.assertEqual(self.tree, back_tree)

    def test_to_newick2(self):
        """Test without quoting."""
        serializer = NewickSerializer(quote_name=False)
        result = serializer.dumps(self.tree)
        expected = ("(((Oslo)Norway,"
                    "(Stockholm)Sweden,"
                    "(((Helsinki)Helsinki)Helsinki)Finland)Europe,Africa)world;")
        self.assertEqual(expected, result)

        back_tree = serializer.loads(expected)
        self.assertEqual(self.tree, back_tree)

    def test_to_newick3(self):
        """Test with data."""
        serializer = NewickSerializer(data_field="data")
        result = serializer.dumps(self.tree2)
        expected = ("((('Oslo')'Norway'[&&NHX:abbrev=NO],"
                    "('Stockholm')'Sweden',"
                    "((('Helsinki')'Helsinki')'Helsinki')'Finland')'"
                    "Europe'[&&NHX:abbrev=EU],'Africa')'world';")
        self.assertEqual(expected, result)
        back_tree = serializer.loads(expected)
        self.assertEqual(self.tree2.to_string(), back_tree.to_string())

    def test_to_newick4(self):
        """Test with data."""
        serializer = NewickSerializer(fields=["data"], escape_comments=True)
        result = serializer.dumps(self.tree2)
        recovered_tree = serializer.loads(result)

        # Recover from string
        for node in recovered_tree.nodes:
            node.data = ast.literal_eval(node.data)

        self.assertEqual(self.tree2.to_string(), recovered_tree.to_string())

    def test_to_newick5(self):
        """Test with distances."""
        serializer = NewickSerializer(data_field="data", quote_name=False)
        result = serializer.dumps(self.tree3)
        expected = ('(((Oslo)Norway:1.2345,'
                    '(Stockholm)Sweden,'
                    '(((Helsinki)Helsinki)Helsinki)Finland)Europe:5.0,'
                    'Africa:1.0)world:0.0;')
        self.assertEqual(expected, result)
        back_tree = serializer.loads(expected)
        self.assertEqual(self.tree3.to_string(), back_tree.to_string())

    def test_from_newick1(self):
        # wikipedia example
        serializer = NewickSerializer()
        tree = serializer.loads("(A,B,(C,D)E)F;")
        result = tree.to_string(style='square')
        expected = ('F\n'
                    '├─ A\n'
                    '├─ B\n'
                    '└─ E\n'
                    '   ├─ C\n'
                    '   └─ D\n')
        self.assertEqual(expected, result)

    def test_from_newick2(self):
        # wikipedia example
        serializer = NewickSerializer()
        tree = serializer.loads("(A,B,(C,D));")
        result = tree.to_string()
        descendants = list(tree.iter_descendants())
        self.assertEqual(5, len(descendants))
        self.assertEqual(3, len(tree.children))

        for letter in "ABCD":
            self.assertIn(letter, [d.identifier for d in descendants])

    @staticmethod
    def remove_anonymous(line):
        return re.sub(r"\d{7,}", '', line)

    def test_from_newick3(self):
        # wikipedia example
        serializer = NewickSerializer()
        tree = serializer.loads("(,,(,));")
        lines = tree.to_string(style='square').splitlines()
        result = [self.remove_anonymous(line) for line in lines]
        expected = ['', '├─ ', '├─ ', '└─ ', '   ├─ ', '   └─ ']
        self.assertEqual(expected, result)

    def test_from_newick4(self):
        # wikipedia example
        newick = "(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"
        serializer = NewickSerializer(data_field="data")
        tree = serializer.loads(newick)
        lines = tree.to_string(style='square').splitlines()
        result = [self.remove_anonymous(line) for line in lines]
        expected = ['',
                    '├─ A',
                    "│  {'distance': 0.1}",
                    '├─ B',
                    "│  {'distance': 0.2}",
                    '└─ ',
                    "   {'distance': 0.5}",
                    '   ├─ C',
                    "   │  {'distance': 0.3}",
                    '   └─ D',
                    "      {'distance': 0.4}"]
        self.assertEqual(expected, result)

    def test_from_newick_quoted(self):
        newick = "why''node('this''node')"
        serializer = NewickSerializer(data_field="data")
        tree = serializer.loads(newick)
        result = tree.to_string(style='square')
        expected = "why''node\n└─ this'node\n"
        self.assertEqual(expected, result)

    def test_from_newick_malformed(self):
        tree = Node({"closing": "]"}, identifier='simple_node')
        nwk = tree.to_newick(escape_comments=False)
        self.assertEqual("'simple_node'[&&NHX:closing=]];", nwk)

        with self.assertRaises(NewickError):
            Node.from_newick(nwk)

    def test_from_newick_escaped(self):
        tree = Node({"closing": "]"}, identifier='simple_node')
        nwk = tree.to_newick(escape_comments=True)
        self.assertEqual("'simple_node'[&&NHX:closing=&rsqb;];", nwk)
        tree_restored = Node.from_newick(nwk)
        self.assertEqual(tree, tree_restored)
