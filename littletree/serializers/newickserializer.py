import io
import os
import re
from typing import TypeVar, Optional, Sequence, Callable

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

    def loads(self, text: str, root: TNode = None) -> TNode:
        file = io.BytesIO(text.encode('utf-8'))
        file = io.BufferedReader(file)
        return self.load(file, root)

    def load(self, file, root: TNode = None) -> TNode:
        if isinstance(file, str):
            file = io.BytesIO(file.encode('utf-8'))
            file = io.BufferedReader(file)
        elif not hasattr(file, "read"):
            file = io.open(file, mode="rb")
        tree = self._parse_subtree(file)
        if root is not None:
            root.update(tree, mode="consume", check_loop=False)
            tree = root
        return tree

    def _parse_subtree(self, file):
        comments = self._parse_comments_whitespace(file)
        children = self._parse_children(file)
        comments.extend(self._parse_comments_whitespace(file))
        node = self._parse_node(file)
        comments.extend(self._parse_comments_whitespace(file))
        distance = self._parse_distance(file)
        comments.extend(self._parse_comments_whitespace(file))

        if distance is not None and self.distance_field is not None:
            self._apply_distance(node, distance)
        if comments:
            self._apply_comments(node, comments)
        if children:
            node.update(children)
        return node

    def _parse_comments_whitespace(self, file):
        comments = list()
        self._skip_whitespace(file)
        while comment := self._parse_comment(file):
            comments.append(comment)
            self._skip_whitespace(file)
        return comments

    def _parse_children(self, file):
        if file.peek(1).startswith(b'('):
            children = []
            while file.read(1) != b')':
                if child := self._parse_subtree(file):
                    children.append(child)
            return children

    def _parse_node(self, file):
        name = self._parse_quoted(file) or self._parse_unquoted(file)
        node = self.factory(identifier=name)
        if name is None:
            node.identifier = hex(id(node))
        return node

    def _parse_distance(self, file):
        if file.peek(1).startswith(b':'):
            file.seek(1, os.SEEK_CUR)
            self._parse_comments_whitespace(file)
            num_str = bytearray()
            while (char := file.read(1)).isdigit() or char in b".+-":
                num_str.append(char[0])
            file.seek(-1, os.SEEK_CUR)
            return float(num_str.decode('utf-8'))

    def _apply_distance(self, node, distance):
        try:
            setattr(node, self.distance_field, distance)
        except AttributeError as e:
            if isinstance(self.fields, str):
                getattr(node, self.fields)[self.distance_field] = distance
            else:
                raise Exception(f"{self.distance_field} is not available on {node}") from e

    def _apply_comments(self, node, comments):
        comment_field = self.comment_field

        pure_comments = []
        for comment in comments:
            if self.use_nhx and comment.startswith("&&NHX"):
                self._apply_nhx(node, comment)
            else:
                pure_comments.append(comment)
        if comment_field is not None:
            comment = "|".join(pure_comments)
            try:
                setattr(node, comment_field, comment)
            except AttributeError as e:
                if isinstance(self.fields, str):
                    getattr(node, self.fields)[comment_field] = comment
                else:
                    raise Exception(f"{self.fields} is not available on {node}") from e

    def _apply_nhx(self, node, text):
        fields = self.fields
        if match := NHX_PATTERN.match(text):
            item_str = match["items"]
            items = dict(item.split("=") for item in item_str.split(":") if len(item) > 1)
            if isinstance(fields, str):
                data = getattr(node, fields)
                data.update(items)
            else:
                for field in fields:
                    try:
                        setattr(node, field, items[field])
                    except KeyError:
                        pass
        else:
            raise ValueError(f"Unable to parse {text!r} as New Hampshire X format")

    def _parse_quoted(self, file):
        if file.peek(1).startswith(SINGLE):
            file.seek(1, os.SEEK_CUR)
            name = []
            tokens = [file.read(1), file.peek(1)]
            while tokens[1] and (tokens[0] != SINGLE or tokens[1].startswith(SINGLE)):
                if tokens[0] == SINGLE:
                    name.append(SINGLE)
                    file.read(1)
                else:
                    name.append(tokens[0])
                tokens = [file.read(1), file.peek(1)]
            return b"".join(name).decode('utf-8')

    def _parse_unquoted(self, file):
        disallowed = b"()[]:;,"
        name = []
        char = file.read(1)
        while char and not char.isspace() and char not in disallowed:
            name.append(char)
            char = file.read(1)
        file.seek(-1, os.SEEK_CUR)
        if name:
            return b"".join(name).decode('utf-8')

    @staticmethod
    def _parse_comment(file):
        if file.peek(1).startswith(b"["):
            file.seek(1, os.SEEK_CUR)
            data_string = []
            char = file.read(1)
            while char and char != b"]":
                data_string.append(char)
                char = file.read(1)
            return b"".join(data_string).decode('utf-8')

    @staticmethod
    def _skip_whitespace(file):
        while file.peek(1).isspace():
            file.seek(1, os.SEEK_CUR)

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
