import io
import operator
from collections import namedtuple
from typing import Union, Callable

from basenode import BaseNode


class StringExporter:
    def __init__(
        self,
        str_factory: Union[str, Callable[[BaseNode], str]] = None,
        continued="├──",
        vertical="│  ",
        end="└──"
    ):
        """
        :param str_factory: How to display each node
        :param continued: Sign for continued branch
        :param vertical: Sign for vertical line
        :param end: Sign for last branch
        """

        if str_factory is None:
            str_factory = str
        elif isinstance(str_factory, str):
            str_factory = operator.attrgetter(str_factory)
        elif not callable(str_factory):
            raise TypeError("str_factory should be callable")

        if not(len(continued) == len(vertical) == len(end)):
            raise ValueError("continued, vertical and end should have some length")

        self.str_factory = str_factory
        self.continued = continued
        self.vertical = vertical
        self.end = end

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
        empty = " " * len(self.continued)
        path = list()
        indent = []

        last_nodes = {id(root)}

        for node, item in root.iter_tree(keep=keep, node_only=False):
            level, index = item.level, item.index

            if level + 1 > len(path):
                path.append(node)

                if level > 1:
                    indent[-1] = empty if id(node.parent) in last_nodes else self.vertical

                indent.append("")
            else:
                path[level] = node
                del path[level + 1:]
                del indent[level + 1:]

            fill = indent[:]

            if level > 0:
                if index == len(node.parent.children) - 1:
                    indent[-1] = self.end
                    fill[-1] = empty
                    last_nodes.add(id(node))
                else:
                    indent[-1] = self.continued
                    fill[-1] = self.vertical

            indent_str = " ".join(indent)
            fill_str = " ".join(fill)
            yield StringItem(indent_str, fill_str, node)


StringItem = namedtuple("StringItem", ["indent", "fill", "node"])
