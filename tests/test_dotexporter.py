from unittest import TestCase

import littletree


class TestDotExporter(TestCase):
    def test_to_dot(self):
        tree = littletree.Node.from_newick("A(b, c, d)")
        result = tree.to_dot()
        expected = (
            'digraph tree {\n'
            '"/A"[label="A"];\n'
            '"/A/b"[label="b"];\n'
            '"/A/c"[label="c"];\n'
            '"/A/d"[label="d"];\n'
            '"/A" -> "/A/b";\n'
            '"/A" -> "/A/c";\n'
            '"/A" -> "/A/d";\n'
            '}')
        self.assertEqual(expected, result)
