from unittest import TestCase

import littletree
from littletree.exporters import MermaidExporter


class TestMermaidExporter(TestCase):
    def test_to_mermaid(self):
        tree = littletree.Node.from_newick("A(b, c, d)")
        exporter = MermaidExporter(node_name="path")
        result = exporter.to_mermaid(tree)
        expected = (
            'graph TD;\n'
            '/A["A"];\n'
            '/A/b["b"];\n'
            '/A/c["c"];\n'
            '/A/d["d"];\n'
            '/A-->/A/b;\n'
            '/A-->/A/c;\n'
            '/A-->/A/d;')
        self.assertEqual(expected, result)
        print(result)
