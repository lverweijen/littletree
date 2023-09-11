import io
import os
import re
from typing import TypeVar, Optional, Sequence, Callable, Union

from littletree import BaseNode

TNode = TypeVar("TNode", bound=BaseNode)
SINGLE = b"'"
DOUBLE = b'"'

NHX_PATTERN = re.compile(r"\&\&NHX(?P<items>(\:[^=]+=[^:]+)*)$")


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
        use_nhx: bool = True,
        quote_name: bool = True,
        distance_field: Optional[str] = "distance",
        comment_field: Optional[str] = None,
    ):
        """
        Create a serializer
        :param factory: How to construct a node
        :param fields: Which fields to use
        :param use_nhx: Whether fields should be in NHX format or pure Newick
        :param quote_name: Whether identifiers should be quoted
        :param distance_field: Which field of node to use for distance if any
        :param comment_field: Which field of node to use for comment if any
        """
        if factory is None:
            from ..node import Node
            factory = Node

        self.factory = factory
        self.fields = fields
        self.use_nhx = use_nhx
        self.quote_name = quote_name
        self.distance_field = distance_field
        self.comment_field = comment_field

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
        if isinstance(self.fields, str):
            editor = DataNodeEditor(self.fields, self.distance_field, self.comment_field)
        else:
            editor = FieldNodeEditor(self.fields, self.distance_field, self.comment_field)

        return NewickParser(file, self.factory, editor, use_nhx=self.use_nhx).run()

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
        fields = self.fields
        quote_name = self.quote_name

        previous_depth = 0
        for node, item in tree.iter_tree(order="post", with_item=True):
            if item.depth >= previous_depth:
                if previous_depth:
                    file.write(",")
                bracket_left = (item.depth - previous_depth) * "("
                file.write(bracket_left)
            else:
                file.write((previous_depth - item.depth) * ")")

            if quote_name:
                file.write(self._quote_name(node.identifier))
            else:
                file.write(str(node.identifier))

            if isinstance(fields, str):
                data = getattr(node, fields)
            elif fields:
                data = {field: getattr(node, field) for field in fields}
            else:
                data = None

            if data:
                data = data.copy()
                comment = data.pop(self.comment_field, None)
                distance = data.pop(self.distance_field, None)

                if distance is not None:
                    file.write(f":{distance}")
                if data and self.use_nhx:
                    self._write_nhx_data(data, file)
                if comment and self.comment_field:
                    file.write(f'[{comment}]')

            previous_depth = item.depth

        file.write(';')

    @staticmethod
    def _write_nhx_data(data, file):
        file.write("[&&NHX")
        for k, v in data.items():
            file.write(f":{k}={v}")
        file.write("]")

    @staticmethod
    def _quote_name(name):
        name_esc = str(name).replace("'", "''")
        return f"'{name_esc}'"


class NewickParser:
    __slots__ = "file", "factory", "editor", "use_nhx", "stack", "nodes", "in_distance"

    def __init__(self, file, factory, editor, use_nhx):
        self.file = io.BufferedReader(file)
        self.factory = factory
        self.editor = editor
        self.use_nhx = use_nhx

        self.stack = []
        self.nodes = [factory()]
        self.in_distance = False

    def run(self):
        table = {
            ord('['): self._read_comment,
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
            print("self.stack = {!r}".format(self.stack))
            raise NewickDecodeError(f"Children on level {len(stack)} have not been closed by ).")

    def _stop(self, _byte):
        self.file.seek(0, os.SEEK_END)

    def _read_comment(self, _byte):
        file = self.file
        comment_bytes = bytearray()
        char = file.read(1)
        while char and char != b"]":
            comment_bytes += char
            char = file.read(1)
        comment = comment_bytes.decode('utf-8')

        node = self.nodes[-1]
        if self.use_nhx and (match := NHX_PATTERN.match(comment)):
            try:
                item_str = match["items"]
                items = dict(item.split("=") for item in item_str.split(":") if len(item) > 1)
            except Exception as err:
                msg = "Invalid New Hampshire Extended-pattern: " + comment
                raise NewickDecodeError(msg) from err
            else:
                self.editor.apply_items(node, items)
        else:
            self.editor.apply_comment(node, comment)

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
            self.editor.apply_distance(node, distance)
        else:
            node.identifier = unquoted_str

    def _read_distance(self, _byte):
        self.in_distance = True


class DataNodeEditor:
    def __init__(self, fields, distance_field, comment_field):
        self.fields = fields
        self.distance_field = distance_field
        self.comment_field = comment_field

    def apply_distance(self, node, distance):
        getattr(node, self.fields)[self.distance_field] = distance

    def apply_comment(self, node, comment):
        comment_field = self.comment_field
        data = getattr(node, self.fields)
        if comment_field in data:
            data[comment_field] += f"|{comment}"
        else:
            data[comment_field] = comment

    def apply_items(self, node, items):
        data = getattr(node, self.fields)
        data.update(items)


class FieldNodeEditor:
    def __init__(self, fields, distance_field, comment_field):
        self.fields = fields
        self.distance_field = distance_field
        self.comment_field = comment_field

    def apply_distance(self, node, distance):
        setattr(node, self.distance_field, distance)

    def apply_comment(self, node, comment):
        comment_field = self.comment_field
        if existing_comment := getattr(node, comment_field):
            comment = existing_comment + f"|{comment}"
            setattr(node, comment_field, comment)
        else:
            setattr(node, comment_field, comment)

    def apply_items(self, node, items):
        existing_fields = self.fields
        for field, value in items.items():
            if field in existing_fields:
                setattr(node, field, items[value])


class NewickDecodeError(Exception):
    pass
