import dataclasses
import io
import os
import re
import xml.sax.saxutils
from typing import TypeVar, Sequence, Callable, Union, Mapping, Optional

from littletree import BaseNode
from littletree.serializers._nodeeditor import get_editor

TNode = TypeVar("TNode", bound=BaseNode)
SINGLE = b"'"
DOUBLE = b'"'

# NHX_PATTERN = re.compile(r"\&\&NHX(?P<items>(\:[^=]+=[^:]+)*)$")
ITEM_PATTERN = re.compile(r"(?P<items>(\:[^=]+=[^:]+)*)$")



@dataclasses.dataclass
class Dialect:
    """
    nhx_prefix: Prefix in comments for nhx-style properties
    quote_name: Whether identifiers should be quoted
    escape_comments: Whether symbols "[]:=" in comments should be escaped.
    """
    nhx_prefix: Optional[str] = "&&NHX"
    quote_name: bool = True
    escape_comments: bool = True


DEFAULT_DIALECTS = {
    "newick": Dialect(nhx_prefix=None, escape_comments=False),
    "nhx": Dialect(escape_comments=False),
    "littletree": Dialect(escape_comments=True),  # Fully serializable (for strings)
}


class NewickSerializer:
    """
    Serialize to/from the newick tree format.
    A formal description is here: http://biowiki.org/wiki/index.php/Newick_Format

    An extension called New Hampshire X format is supported and enabled by default.
    This extension is described here: https://www.cs.mcgill.ca/~birch/doc/forester/NHX.pdf
    It can be disabled by setting `use_nhx` to False.
    """
    def __init__(
        self,
        factory: Callable[[], TNode] = None,
        fields: Sequence[str] = (),
        data_field: str = None,
        dialect: Union[str, Dialect, Mapping] = None,
        **kwargs,
    ):
        """
        Create a serializer
        :param factory: How to construct a node
        :param fields: Which fields to use (distance and comment might be useful)
        :param data_field: Use one field for everything
        :param dialect: Dialect options
        :param kwargs: Alternative way of specifying dialect options
        """
        if factory is None:
            from ..node import Node
            factory = Node

        if not dialect:
            dialect = Dialect(**kwargs)
        elif isinstance(dialect, str):
            dialect = DEFAULT_DIALECTS[dialect]
        else:
            dialect = Dialect(**dialect)

        self.factory = factory
        self.editor = get_editor(fields, data_field)
        self.dialect = dialect

    def loads(self, text: Union[str, bytes, bytearray], root: TNode = None) -> TNode:
        if isinstance(text, str):
            text = text.encode('utf-8')
        file = io.BytesIO(text)
        return self.load(file, root)

    def load(self, file, root: TNode = None) -> TNode:
        if not hasattr(file, "read"):
            with open(file, mode="rb") as reader:
                tree = self._load(reader)
        else:
            tree = self._load(file)

        if root is not None:
            root.update(tree, mode="detach", check_loop=False)
            tree = root
        return tree

    def _load(self, file):
        return NewickParser(file, self.factory, self.dialect, self.editor).run()

    def dumps(self, tree: TNode):
        file = io.StringIO()
        self.dump(tree, file)
        return file.getvalue()

    def dump(self, tree: TNode, file):
        if hasattr(file, "write"):
            self._to_newick(tree, file)
        else:
            with open(file, "w") as writer:
                self._to_newick(tree, writer)

    def _to_newick(self, tree: TNode, file):
        dialect = self.dialect

        previous_depth = 0
        for node, item in tree.iter_tree(order="post", with_item=True):
            if item.depth >= previous_depth:
                if previous_depth:
                    file.write(",")
                bracket_left = (item.depth - previous_depth) * "("
                file.write(bracket_left)
            else:
                file.write((previous_depth - item.depth) * ")")

            if dialect.quote_name:
                file.write(self._quote_name(node.identifier))
            else:
                file.write(str(node.identifier))

            if data := self.editor.get_attributes(node):
                data = data.copy()
                comment = data.pop("comment", None)
                distance = data.pop("distance", None)

                if distance is not None:
                    file.write(f":{distance}")
                if data and dialect.nhx_prefix:
                    self._write_nhx_data(data, file, dialect)
                if comment:
                    if dialect.escape_comments:
                        comment = escape_comment(comment)
                    file.write(f'[{comment}]')

            previous_depth = item.depth

        file.write(';')

    @staticmethod
    def _write_nhx_data(data, file, dialect: Dialect):
        file.write("[")
        file.write(dialect.nhx_prefix)
        if dialect.escape_comments:
            for k, v in data.items():
                file.write(f":{escape_comment(str(k))}={escape_comment(str(v))}")
        else:
            for k, v in data.items():
                file.write(f":{k}={v}")
        file.write("]")

    @staticmethod
    def _quote_name(name):
        name_esc = str(name).replace("'", "''")
        return f"'{name_esc}'"


class NewickParser:
    __slots__ = "file", "factory", "dialect", "editor", "stack", "nodes", "in_distance"

    def __init__(self, file, factory, dialect, editor):
        self.file = io.BufferedReader(file)
        self.factory = factory
        self.dialect = dialect
        self.editor = editor

        self.stack = []
        self.nodes = [factory()]
        self.in_distance = False

    def run(self):
        table = {
            ord('['): self._read_comment,
            ord(']'): self._unmatched_bracket,
            ord(','): self._read_sibling,
            ord('('): self._read_children,
            ord(')'): self._read_parent,
            ord("'"): self._read_quoted,
            ord(":"): self._read_distance,
            ord(';'): self._stop,
        }
        unquoted_name = self._read_unquoted

        buffer = self.file
        while byte := buffer.read(1):
            if not byte.isspace():
                table.get(byte[0], unquoted_name)(byte)

        nodes, stack = self.nodes, self.stack
        if len(nodes) == 1 and not stack:
            [node] = nodes
            return node
        elif len(nodes) != 1:
            raise NewickDecodeError(f"There should be one root, but {len(nodes)} were defined.")
        else:
            raise NewickDecodeError(f"Children on level {len(stack)} have not been closed by ).")

    def _stop(self, _byte):
        self.file.seek(0, os.SEEK_END)

    def _read_comment(self, _byte):
        dialect = self.dialect
        file = self.file
        comment_bytes = bytearray()
        depth = 1
        while char := file.read(1):
            if char == b"[":
                depth += 1
            elif char == b"]":
                depth -= 1
            if depth:
                comment_bytes += char
            else:
                break
        comment = comment_bytes.decode('utf-8')

        node = self.nodes[-1]
        nhx_prefix = dialect.nhx_prefix
        if (nhx_prefix and comment.startswith(nhx_prefix)
                and (match := ITEM_PATTERN.match(comment.removeprefix(nhx_prefix)))):
            try:
                item_str = match["items"]
                items = dict(item.split("=") for item in item_str.split(":") if len(item) > 1)
            except Exception as err:
                msg = "Invalid New Hampshire Extended-pattern: " + comment
                raise NewickDecodeError(msg) from err
            else:
                if dialect.escape_comments:
                    items = {unescape_comment(k): unescape_comment(v)
                             for k, v in items.items()}
                self.editor.update(node, items)
        else:
            if dialect.escape_comments:
                comment = unescape_comment(comment)
                if existing_comment := self.editor.get(node, comment):
                    comment = f"{existing_comment}|{comment}"
                self.editor.set(node, "comment", comment)

    def _unmatched_bracket(self, _byte):
        raise NewickDecodeError("Brackets [ and ] don't match.")

    def _read_children(self, _byte):
        self.stack.append(self.nodes)
        self.nodes = [self.factory()]
        self.in_distance = False

    def _read_parent(self, _byte):
        children = self.nodes
        self.nodes = self.stack.pop()
        self.nodes[-1].update(children)
        self.in_distance = False

    def _read_sibling(self, _byte):
        self.nodes.append(self.factory())
        self.in_distance = False

    def _read_quoted(self, _byte):
        file = self.file
        name_bytes = bytearray()
        tokens = [file.read(1), file.peek(1)]
        while tokens[1] and (tokens[0] != SINGLE or tokens[1].startswith(SINGLE)):
            if tokens[0] == SINGLE:
                name_bytes += SINGLE
                file.read(1)
            else:
                name_bytes += tokens[0]
            tokens = [file.read(1), file.peek(1)]
        name = name_bytes.decode('utf-8')
        self.nodes[-1].identifier = name

    def _read_unquoted(self, byte):
        file = self.file
        disallowed = set(b"()[]:;,")
        unquoted_bytes = bytearray()
        while byte and not byte.isspace() and byte[0] not in disallowed:
            unquoted_bytes += byte
            byte = file.read(1)
        file.seek(-1, os.SEEK_CUR)
        unquoted_str = unquoted_bytes.decode("utf-8")

        node = self.nodes[-1]
        if self.in_distance:
            distance = float(unquoted_str)
            self.editor.set(node, "distance", distance)
        else:
            node.identifier = unquoted_str

    def _read_distance(self, _byte):
        self.in_distance = True


class NewickDecodeError(Exception):
    pass


ESCAPE_COMMENTS = {
    "[": "&lsqb;",
    "]": "&rsqb;",
    "=": "&equals;",
    ":": "&colon;"
}
UNESCAPE_COMMENTS = {v: k for (k, v) in ESCAPE_COMMENTS.items()}


def escape_comment(raw_comment):
    return xml.sax.saxutils.escape(raw_comment, ESCAPE_COMMENTS)


def unescape_comment(escaped_comment):
    return xml.sax.saxutils.unescape(escaped_comment, UNESCAPE_COMMENTS)
