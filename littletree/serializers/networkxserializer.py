from typing import TypeVar, Callable, Sequence

from ._nodeeditor import get_editor
from ..basenode import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)


class NetworkXSerializer:
    def __init__(
        self,
        factory: Callable[[], TNode] = None,
        fields: Sequence[str] = (),
        data_field: str = None,
    ):
        self.factory = factory
        self.editor = get_editor(fields, data_field)

    def from_networkx(self, graph):
        from . import RelationSerializer
        import networkx as nx
        graph: nx.DiGraph
        editor = self.editor

        if not nx.is_arborescence(graph):
            raise ValueError(f"graph {graph} is not an (arborescent) tree")

        serializer = RelationSerializer(factory=self.factory)
        edges = [dict(parent=p, identifier=c) for (p, c) in graph.edges]
        contained_tree = serializer.from_relations(edges)
        [tree] = contained_tree.children
        tree.detach()

        data = graph.nodes.data()
        if data:
            for node in tree.iter_nodes():
                editor.update(node, data[node.identifier])

        return tree

    def to_networkx(self, tree: TNode):
        import networkx as nx
        editor = self.editor

        edges = [(node.parent.identifier, node.identifier) for node in tree.iter_descendants()]
        graph = nx.DiGraph(edges)
        node_attributes = {n.identifier: editor.get_attributes(n) for n in tree.iter_nodes()}
        nx.set_node_attributes(graph, node_attributes)
        return graph
