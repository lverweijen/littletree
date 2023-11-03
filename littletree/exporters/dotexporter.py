import io
import operator
import subprocess
from pathlib import Path
from typing import Mapping, Callable, Any, Union, TypeVar

try:
    from PIL import Image
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False

from ..basenode import BaseNode


TNode = TypeVar("TNode", bound=BaseNode)
NodeAttributes = Union[Mapping[str, Any], Callable[[TNode], Mapping[str, Any]]]
EdgeAttributes = Union[Mapping[str, Any], Callable[[TNode, TNode], Mapping[str, Any]]]
GraphAttributes = Mapping[str, Any]


class DotExporter:
    def __init__(
        self,
        node_name: Union[str, Callable[[TNode], str], None] = "path",
        node_attributes: NodeAttributes = None,
        edge_attributes: EdgeAttributes = None,
        graph_attributes: GraphAttributes = None,
        directed: bool = True,
        dot_path: Path = "dot",
    ):
        def default_node_name(node):
            return hex(id(node))

        if not node_name:
            node_name = default_node_name
        elif isinstance(node_name, str):
            node_name = operator.attrgetter(node_name)
        elif not callable(node_name):
            raise TypeError("node_name should be callable")

        self.node_name = node_name
        self.node_attributes = node_attributes
        self.edge_attributes = edge_attributes
        self.graph_attributes = graph_attributes
        self.directed = directed
        self.dot_path = Path(dot_path)

    def to_image(self, tree: TNode, file=None, keep=None, file_format=None, as_bytes=False):
        """Export tree to an image

        If file is None and not as_bytes, it will return a Pillow object [default].
        If file is None and as_bytes, it will return image as bytes.
        """
        if hasattr(file, "write"):
            self._to_image(tree, file, keep, file_format)
        elif file:
            filepath = Path(file)
            with open(filepath, "bw") as file:
                self._to_image(tree, file, keep, file_format or filepath.suffix[1:])
        else:
            img_bytes = self._to_image(tree, subprocess.PIPE, keep, file_format)
            if as_bytes:
                return img_bytes
            elif _HAS_PILLOW:
                # Pillow doesn't support streaming, so buffering bytes is fine.
                return Image.open(io.BytesIO(img_bytes))
            else:
                raise ImportError("Pillow not installed. Use `pip install Pillow`.")

    def _to_image(self, tree, file, keep, file_format):
        if not file_format:
            file_format = "png"

        try:
            args = [self.dot_path, "-T", file_format]
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=file)
        except FileNotFoundError as err:
            raise Exception("Install dot from graphviz.org") from err

        self.to_dot(tree, io.TextIOWrapper(process.stdin, encoding='utf-8'), keep=keep)
        process.stdin.close()
        (output, errors) = process.communicate()
        if process.returncode != 0:
            raise Exception(errors.decode('utf-8', errors="replace"))
        return output

    def to_dot(self, tree: TNode, file=None, keep=None):
        output = self._to_dot(tree, keep)

        if file is None:
            return "\n".join(output)
        elif hasattr(file, "write"):
            file.writelines(output)
        else:
            with open(file, "w", encoding='utf-8') as fp:
                fp.writelines(output)

    def _to_dot(self, root, keep=None):
        name_factory = self.node_name
        escape_string = self._escape_string
        handle_attributes = self._handle_attributes

        graph_attributes = self.graph_attributes
        node_static, node_dynamic = self._split_attributes(self.node_attributes)
        edge_static, edge_dynamic = self._split_attributes(self.edge_attributes)

        if self.directed:
            yield "digraph tree {"
            arrow = "->"
        else:
            yield "graph tree {"
            arrow = "--"

        if graph_attributes:
            attrs = handle_attributes(graph_attributes, root)
            yield f"graph{attrs};"
        if node_static:
            attrs = handle_attributes(node_static, root)
            yield f"node{attrs};"
        if edge_static:
            attrs = handle_attributes(edge_static, root, root)
            yield f"edge{attrs};"

        for node in root.iter_tree(keep):
            node_name = escape_string(str(name_factory(node)))
            attrs = handle_attributes(node_dynamic, node)
            yield f"{node_name}{attrs};"
        for node in root.iter_descendants(keep):
            parent_name = escape_string(str(name_factory(node.parent)))
            child_name = escape_string(str(name_factory(node)))
            attrs = handle_attributes(edge_dynamic, node.parent, node)
            yield f"{parent_name}{arrow}{child_name}{attrs};"
        yield "}"

    @classmethod
    def _split_attributes(cls, attributes: Union[NodeAttributes, EdgeAttributes]):
        if isinstance(attributes, Mapping):
            static = {k: v for (k, v) in attributes.items() if not callable(v)}
            dynamic = {k: v for (k, v) in attributes.items() if callable(v)}
        elif callable(attributes):
            static = None
            dynamic = attributes
        else:
            static = attributes
            dynamic = None
        return static, dynamic

    @classmethod
    def _handle_attributes(
        cls,
        attributes: Union[NodeAttributes, EdgeAttributes, GraphAttributes],
        *args
    ) -> str:
        """
        Attributes can be:
        - Dict [str, (Any | TNode -> Any)]
        - TNode -> Dict[str, Any]

       Also supported, but not recommended:
        - str
        - TNode -> str
        """

        escape_string = cls._escape_string
        if not attributes:
            return ""
        if callable(attributes):
            attributes = attributes(*args)
        if isinstance(attributes, Mapping):
            options = []
            for k, v in attributes.items():
                if callable(v):
                    v = v(*args)
                options.append(f"{k}={escape_string(v)}")
            attributes = "[" + " ".join(options) + "]"
        elif not attributes.startswith("["):
            attributes = f"[{attributes}]"
        return attributes

    @staticmethod
    def _escape_string(arg) -> str:
        if isinstance(arg, str):
            return '"' + arg.replace('"', '\\"') + '"'
        else:
            return arg
