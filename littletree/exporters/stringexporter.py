import io
from typing import Union, Callable, TypedDict

from ..basenode import BaseNode


class Style(TypedDict):
    branch: str
    last: str
    vertical: str


DEFAULT_STYLES = {
    "square": Style(branch="├─", last="└─", vertical="│ "),
    "square-4": Style(branch="├──", last="└──", vertical="│  "),
    "square-arrow": Style(branch="├→", last="└→", vertical="│ "),
    "round": Style(branch="├─", last="╰─", vertical="│ "),
    "round-4": Style(branch="├──", last="╰──", vertical="│  "),
    "round-arrow": Style(branch="├→", last="╰→", vertical="│ "),
    "ascii": Style(branch="|--", last="`--", vertical="|  "),
    "ascii-arrow": Style(branch="|->", last="`->", vertical="|  "),
    "list": Style(branch="-", last="-", vertical=" "),
}


class StringExporter:
    def __init__(
        self,
        formatter: Union[str, Callable[[BaseNode], str]] = None,
        style: Union[Style, str] = "square",
    ):
        """
        :param formatter: How to display each node.
        If it's a string, `formatter.format(node=node)` will be called on each node.
        :param style: Mapping with following keys:
        - branch: Sign for continued branch
        - last: Sign for last branch
        - vertical: Sign for vertical line
        """

        if formatter is None:
            formatter = str
        elif isinstance(formatter, str):
            format_str = formatter

            def formatter(node):
                return format_str.format(node=node)
        elif not callable(formatter):
            raise TypeError("format should be a formatting string or a callable")

        if isinstance(style, str):
            if style in DEFAULT_STYLES:
                style = DEFAULT_STYLES[style]
            else:
                default_styles = ", ".join(DEFAULT_STYLES.keys())
                raise ValueError(f"Available default styles are: {default_styles}")
        elif not(len(style["branch"]) == len(style["vertical"]) == len(style["last"])):
            raise ValueError("branch, vertical and last should have same length")

        self.formatter = formatter
        self.style = style

    def to_string(self, node, file=None, keep=None):
        if file is None:
            file = io.StringIO()
            self._to_string(node, file, keep)
            return file.getvalue()
        elif not hasattr(file, "write"):
            with open(file, "w", encoding='utf-8') as writer:
                self._to_string(node, writer, keep)
        else:
            self._to_string(node, file, keep)

    def _to_string(self, node, file, keep):
        formatter = self.formatter
        write_indent = self._write_indent
        style = self.style
        empty_style = len(style["last"]) * " "
        lookup1 = [empty_style, style["vertical"]]
        lookup2 = [style["last"], style["branch"]]

        for pattern, node in self._iterate_patterns(node, keep=keep):
            for i, line in enumerate(formatter(node).splitlines()):
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
            del pattern[item.depth - 1:]
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
