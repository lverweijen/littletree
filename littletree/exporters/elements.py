class Literal:
    """Literal value to insert into Graphviz or Mermaid."""
    __slots__ = "value"

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
