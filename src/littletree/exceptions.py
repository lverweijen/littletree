class TreeException(Exception):
    """Base tree exceptions."""
    pass


class DuplicateParentError(TreeException):
    """Operation would add multiple parents to a node."""
    def __init__(self, node):
        self.node = node

    def __str__(self):
        return (f"{self.node} already has a parent {self.node.parent}. "
                f"Consider calling node.copy() or node.detach() first.")


class DuplicateChildError(TreeException):
    """Operation would add multiple children with the same identifier to the same parent."""
    def __init__(self, node, identifier):
        self.node = node
        self.identifier = identifier

    def __str__(self):
        return f"{self.identifier} is already present in {self.node}"


class LoopError(TreeException):
    """Operation would create a loop."""
    def __init__(self, node, ancestor):
        self.node = node
        self.ancestor = ancestor

    def __str__(self):
        return f"{self.node} can't become parent of {self.ancestor}"
