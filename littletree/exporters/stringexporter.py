import io
import operator
from collections import namedtuple
from typing import Union, Callable, Optional, Mapping

from ..basenode import BaseNode


class StringExporter:
    def __init__(
        self,
        str_factory: Union[str, Callable[[BaseNode], str]] = None,
        style: Optional[Mapping[str, str]] = None,
    ):
        """
        :param str_factory: How to display each node
        :param style: Mapping with following keys:
        - continued: Sign for continued branch
        - vertical: Sign for vertical line
        - end: Sign for last branch
        """

        if str_factory is None:
            str_factory = str
        elif isinstance(str_factory, str):
            str_factory = operator.attrgetter(str_factory)
        elif not callable(str_factory):
            raise TypeError("str_factory should be callable")

        if style is None:
            style = dict(continued="├──",
                         vertical="│  ",
                         end="└──")

        if not(len(style["continued"]) == len(style["vertical"]) == len(style["end"])):
            raise ValueError("continued, vertical and end should have same length")

        self.str_factory = str_factory
        self.style = style

    def to_string(self, node, file=None, keep=None):
        if file is None:
            file = io.StringIO()
            self._to_string(node, file, keep)
            return file.getvalue()
        elif not hasattr(file, "write"):
            with open(file, "wb"):
                self._to_string(node, file, keep)
        else:
            self._to_string(node, file, keep)

    def _to_string(self, node, file, keep):
        str_factory = self.str_factory
        for indent, fill, node in self._to_string_iter(node, keep=keep):
            for i, line in enumerate(str_factory(node).splitlines()):
                if i == 0:
                    file.write(f"{indent} {line}\n")
                else:
                    file.write(f"{fill} {line}\n")

    def _to_string_iter(self, root, keep):
        path = list()
        indent = []

        continued = self.style["continued"]
        vertical = self.style["vertical"]
        end = self.style["end"]
        empty = " " * len(continued)

        last_nodes = {id(root)}

        for node, item in root.iter_tree(keep=keep, with_item=True):
            level, index = item.level, item.index

            if level + 1 > len(path):
                path.append(node)

                if level > 1:
                    indent[-1] = empty if id(node.parent) in last_nodes else vertical

                indent.append("")
            else:
                path[level] = node
                del path[level + 1:]
                del indent[level + 1:]

            fill = indent[:]

            if level > 0:
                if index == len(node.parent.children) - 1:
                    indent[-1] = end
                    fill[-1] = empty
                    last_nodes.add(id(node))
                else:
                    indent[-1] = continued
                    fill[-1] = vertical

            indent_str = " ".join(indent)
            fill_str = " ".join(fill)
            yield StringItem(indent_str, fill_str, node)


StringItem = namedtuple("StringItem", ["indent", "fill", "node"])
