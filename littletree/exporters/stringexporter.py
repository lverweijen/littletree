import io
import operator
from typing import Union, Callable, TypedDict

from ..basenode import BaseNode


class Style(TypedDict):
    continued: str
    vertical: str
    end: str


class StringExporter:
    def __init__(
        self,
        str_factory: Union[str, Callable[[BaseNode], str]] = None,
        style: Style = None,
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
            style = dict(continued="├─", vertical="│ ", end="└─")
        elif not(len(style["continued"]) == len(style["vertical"]) == len(style["end"])):
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
        write_indent = self._write_indent
        style = self.style
        empty_style = len(style["end"]) * " "
        lookup1 = [empty_style, style["vertical"]]
        lookup2 = [style["end"], style["continued"]]

        for pattern, node in self._iterate_patterns(node, keep=keep):
            for i, line in enumerate(str_factory(node).splitlines()):
                if not node.is_root:
                    if i == 0:
                        write_indent(file, pattern, lookup1, lookup2)
                    else:
                        write_indent(file, pattern, lookup1, lookup1)
                    file.write(" ")
                file.write(line)
                file.write("\n")

    @staticmethod
    def _iterate_patterns(root, keep):
        # Yield for each node a list of continuation indicators.
        # The continuation indicator tells us whether the branch at a certain level is continued.
        pattern = []
        yield pattern, root
        for node, item in root.iter_descendants(keep=keep, with_item=True):
            del pattern[item.level - 1:]
            is_continued = item.index < len(node.parent.children) - 1
            pattern.append(is_continued)
            yield pattern, node

    @staticmethod
    def _write_indent(file, pattern, lookup1, lookup2):
        # Based on calculated patterns, this will substitute an indent line
        if pattern:
            for is_continued in pattern[:-1]:
                file.write(lookup1[is_continued])
                file.write(" ")
            file.write(lookup2[pattern[-1]])
