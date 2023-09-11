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
NodeAttributes = Union[Mapping[str, Any], Callable[[TNode], Union[str, Mapping]], str]
EdgeAttributes = Union[Mapping[str, Any], Callable[[TNode, TNode], Union[str, Mapping]], str]


class DotExporter:
    def __init__(
        self,
        name_factory: Union[str, Callable[[TNode], str]] = "path",
        node_attributes: NodeAttributes = None,
        edge_attributes: EdgeAttributes = None,
        dot_path: Path = "dot"
    ):
        if name_factory is None:
            name_factory = str
        elif isinstance(name_factory, str):
            name_factory = operator.attrgetter(name_factory)
        elif not callable(name_factory):
            raise TypeError("name_factory should be callable")

        self.name_factory = name_factory
        self.node_attributes = node_attributes
        self.edge_attributes = edge_attributes
        self.dot_path = Path(dot_path)

    def to_image(self, tree: TNode, file=None, keep=None, file_format="png", as_bytes=False):
        """Export tree to an image

        If file is None and not as_bytes, it will return a Pillow object [default].
        If file is None and as_bytes, it will return image as bytes.
        """
        if hasattr(file, "write"):
            self._to_image(tree, file, keep, file_format)
        elif file:
            with open(file, "bw") as writer:
                self._to_image(tree, writer, keep, file_format)
        else:
            img_bytes = self._to_image(tree, subprocess.PIPE, keep, file_format)
            if as_bytes:
                return img_bytes
            elif _HAS_PILLOW:
                # Pillow doesn't support streaming, so piping from subprocess won't be faster.
                return Image.open(io.BytesIO(img_bytes))
            else:
                raise ImportError("Pillow not installed. Use `pip install Pillow`.")

    def _to_image(self, tree, file, keep, file_format):
        args = [self.dot_path, "-T", file_format]
        try:
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
        node_to_str = self.name_factory
        yield "digraph tree {"
        for node in root.iter_tree(keep):
            node_esc = self._escape_string(str(node_to_str(node)))
            attrs = self._handle_attributes(self.node_attributes, node)
            yield f"{node_esc}{attrs};"
        for node in root.iter_descendants(keep):
            parent_esc = self._escape_string(str(node_to_str(node.parent)))
            child_esc = self._escape_string(str(node_to_str(node)))
            attrs = self._handle_attributes(self.edge_attributes, node.parent, node)
            yield f"{parent_esc} -> {child_esc}{attrs};"
        yield "}"

    @classmethod
    def _handle_attributes(cls, attributes: Callable[[TNode], Union[str, Mapping]], *args):
        if not attributes:
            return ""
        elif callable(attributes):
            attributes = attributes(*args)
        elif isinstance(attributes, Mapping):
            options = []
            for k, v in attributes.items():
                if callable(v):
                    v = v(*args)
                options.append(f"{k}={cls._escape_string(v)}")
            attributes = "[" + " ".join(options) + "]"
        return attributes

    @staticmethod
    def _escape_string(arg) -> str:
        if isinstance(arg, str):
            return '"' + arg.replace('"', '\\"') + '"'
        else:
            return arg
