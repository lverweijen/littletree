import io
import operator
import subprocess
from pathlib import Path
from typing import Callable, Union, TypeVar, Tuple, Optional

from .elements import Literal

TNode = TypeVar("TNode", bound="NodeMixin")
TShape = Union[
    Tuple[str, str], str,
    Callable[[TNode], Union[Tuple[str, str], str]]
]

# Provide normal names for shapes (dot syntax is saner than mermaid)
DEFAULT_SHAPES = {
    "box": ("[", "]"),
    "rectangle": ("[", "]"),
    "round": ("(", ")"),
    "stadium": ("([", "])"),
    "subroutine": ("[[", "]]"),
    "asymmetric": (">", "]"),
    "circle": ("((", "))"),
    "double-circle": ("(((", ")))"),
    "rhombus": ("{", "}"),
    "hexagon": ("{{", "}}"),
    "parallelogram": ("[/", "/]"),
    "inv-parallelogram": ("[\\", r"\]"),
    "trapezium": ("[/", r"\]"),
    "inv-trapezium": ("[\\", "/]"),
}


class MermaidExporter:
    """Exporter for mermaid diagrams."""
    def __init__(
        self,
        node_name: Union[str, Callable[[TNode], str], None] = None,
        node_label: Union[str, Callable[[TNode], str], None] = str,
        node_shape: TShape = "box",
        edge_arrow: Union[str, Callable[[TNode, TNode], str]] = "-->",
        graph_direction: str = "TD",
        mermaid_path: Union[str, Path] = "mmdc"
    ):
        def default_node_name(node):
            return hex(id(node))

        self.node_name = self._make_callable(node_name) or default_node_name
        self.node_label = self._make_callable(node_label)
        self.node_shape = node_shape
        self.edge_arrow = edge_arrow
        self.graph_direction = graph_direction
        self.mermaid_path = mermaid_path

    def to_image(self, tree, file, keep=None):
        if not file:
            raise ValueError("Parameter file is required for mermaid")

        try:
            args = [str(self.mermaid_path), "--input", "-", "--output", str(file)]
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError as err:
            raise Exception("Install mermaid-cli from npm") from err

        self.to_mermaid(tree, io.TextIOWrapper(process.stdin, encoding='utf-8'), keep=keep)
        process.stdin.close()
        (output, errors) = process.communicate()
        if process.returncode != 0:
            raise Exception(errors.decode('utf-8', errors="replace"))
        return output

    def to_mermaid(self, tree: TNode, file=None, keep=None):
        output = self._to_mermaid(tree, keep)

        if file is None:
            return "".join(output)
        elif hasattr(file, "write"):
            file.writelines(output)
        else:
            with open(file, "w", encoding='utf-8') as fp:
                fp.writelines(output)

    def _to_mermaid(self, root, keep=None):
        node_name = self.node_name
        node_label = self.node_label
        node_shape = self.node_shape
        edge_arrow = self.edge_arrow
        if isinstance(node_shape, str):
            node_shape = DEFAULT_SHAPES[node_shape]
        get_shape = self._get_shape
        escape_string = self._escape_string

        # Output header
        yield f"graph {self.graph_direction};\n"

        # Output nodes
        for node in root.iter_tree(keep):
            left, right = get_shape(node_shape, node)
            name = node_name(node)
            if node_label:
                text = escape_string(node_label(node))
                yield f"{name}{left}{text}{right};\n"
            else:
                yield f"{name};\n"

        # Output edges
        for node in root.iter_descendants(keep):
            arrow = edge_arrow(node.parent, node) if callable(edge_arrow) else edge_arrow
            parent = node_name(node.parent)
            child = node_name(node)
            yield f"{parent}{arrow}{child};\n"

    @staticmethod
    def _get_shape(shape_factory, node):
        if callable(shape_factory):
            shape = shape_factory(node)
            if isinstance(shape, str):
                shape = DEFAULT_SHAPES[shape]
        else:
            shape = shape_factory
        return shape

    @staticmethod
    def _escape_string(text) -> str:
        if isinstance(text, Literal):
            return str(text)
        text = str(text)
        text = text.replace('#', "#35;")
        text = text.replace('`', "#96;")
        text = text.replace('"', "#quot;")
        return f'"{text}"'

    @staticmethod
    def _make_callable(f) -> Optional[Callable]:
        if not f:
            f = None
        elif isinstance(f, str):
            f = operator.attrgetter(f)
        elif not callable(f):
            raise TypeError(f"Parameter should be callable")
        return f
