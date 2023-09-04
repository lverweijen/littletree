from unittest import TestCase

from littletree import Node
from littletree.serializers.newickserializer import NewickSerializer


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
        serializer = NewickSerializer(fields="data")
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
        serializer = NewickSerializer(fields=["data"])
        result = serializer.dumps(self.tree2)
        expected = ("((('Oslo'[&&NHX:data={}])"
                    "'Norway'[&&NHX:data={'abbrev': 'NO'}],"
                    "('Stockholm'[&&NHX:data={}])'Sweden'[&&NHX:data={}],"
                    "((('Helsinki'[&&NHX:data={}])'Helsinki'[&&NHX:data={}])'Helsinki'[&&NHX:data={}])'Finland'[&&NHX:data={}])"
                    "'Europe'[&&NHX:data={'abbrev': 'EU'}],"
                    "'Africa'[&&NHX:data={}])'world'[&&NHX:data={}];")
        self.assertEqual(expected, result)

        # Round-tripping wouldn't be possible, because NHX may not contain colon-symbol
        # and only supports strings anyway.
        # This testcase is a bit weird anyway

    def test_to_newick5(self):
        """Test with distances."""
        serializer = NewickSerializer(fields="data", quote_name=False)
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
        result = tree.to_string()
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

    def test_from_newick3(self):
        # wikipedia example
        serializer = NewickSerializer()
        tree = serializer.loads("(,,(,));")
        lines = tree.to_string().splitlines()
        result = [line.split('0x')[0] for line in lines]
        expected = ['', '├─ ', '├─ ', '└─ ', '   ├─ ', '   └─ ']
        self.assertEqual(expected, result)

    def test_from_newick4(self):
        # wikipedia example
        newick = "(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"
        serializer = NewickSerializer(fields="data")
        tree = serializer.loads(newick)
        lines = tree.to_string().splitlines()
        result = [line.split('0x')[0] for line in lines]
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
