import operator
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping, Callable, Any, Union, TypeVar

from ..basenode import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)


class DotExporter:
    def __init__(
        self,
        name_factory: Union[str, Callable[[TNode], Any]] = "path",
        node_attributes: Callable[[TNode], Union[str, Mapping]] = None,
        edge_attributes: Callable[[TNode], Union[str, Mapping]] = None,
        separator: str = "/",
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
        self.separator = separator
        self.dot_path = Path(dot_path)

    def to_image(self, node: TNode, picture_filename=None, keep=None, file_format="png"):
        if picture_filename is None:
            try:
                from PIL import Image
            except ImportError:
                raise ImportError("Either install Pillow or supply a filename to save to.")

            with tempfile.NamedTemporaryFile(delete=False, suffix="_DicTree.png") as fp:
                picture_filename = fp.name

            self._to_image(node, picture_filename, keep, file_format)
            img = Image.open(picture_filename)
            return img
        else:
            self._to_image(node, picture_filename, keep, file_format)

    def _to_image(self, node, picture_filename, keep, file_format):
        with tempfile.NamedTemporaryFile(delete=False, suffix="_DicTree.dot") as fp:
            dot_filename = fp.name

        self.to_dot(node, dot_filename=dot_filename, keep=keep)

        cmd = [self.dot_path, dot_filename, "-T", file_format, "-o", picture_filename]
        subprocess.check_call(cmd)
        Path(fp.name).unlink()

    def to_dot(self, root: TNode, dot_filename=None, keep=None):
        output = self._to_dot(root, keep)

        if dot_filename is None:
            return "\n".join(output)
        elif hasattr(dot_filename, "write"):
            for line in output:
                text = line + "\n"
                dot_filename.write(text.encode('utf-8'))
        else:
            with open(dot_filename, "wb") as fp:
                for line in output:
                    text = line + "\n"
                    fp.write(text.encode('utf-8'))

    def _to_dot(self, root, keep=None):
        node_to_str = self.name_factory
        output = ["digraph tree {"]
        for node in root.iter_tree(keep):
            node_esc = self._escape_string(str(node_to_str(node)))
            attrs = self._handle_attributes(self.node_attributes, node)
            output.append(f"{node_esc}{attrs};")
        for node in root.iter_descendants(keep):
            parent_esc = self._escape_string(str(node_to_str(node.parent)))
            child_esc = self._escape_string(str(node_to_str(node)))
            attrs = self._handle_attributes(self.edge_attributes, node.parent, node)
            output.append(f"{parent_esc} -> {child_esc}{attrs};")
        output.append("}")
        return output

    @classmethod
    def _handle_attributes(cls, attributes: Callable[[TNode], Union[str, Mapping]], *args):
        if attributes is None:
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
