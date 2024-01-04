class TreeException(Exception):
    pass


class DuplicateParentError(TreeException):
    def __init__(self, node):
        self.node = node

    def __str__(self):
        return (f"{self.node} already has a parent {self.node.parent}. "
                f"Consider calling node.copy() or node.detach() first.")


class DuplicateChildError(TreeException):
    def __init__(self, node, identifier):
        self.node = node
        self.identifier = identifier

    def __str__(self):
        return f"{self.identifier} is already present in {self.node}"


class LoopError(TreeException):
    def __init__(self, node, ancestor):
        self.node = node
        self.ancestor = ancestor

    def __str__(self):
        return f"{self.node} can't become parent of {self.ancestor}"


class DifferentTreeError(TreeException):
    def __init__(self, root1, root2):
        self.root1 = root1
        self.root2 = root2

    def __str__(self):
        return f"Nodes have different roots: {self.root1} vs {self.root2}"
