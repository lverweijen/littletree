class DuplicateParent(Exception):
    def __init__(self, node):
        self.node = node

    def __str__(self):
        return f"{self.node} already has a parent {self.node.parent}. " \
               f"Consider node.copy(), node.detach() or node.link instead."


class DuplicateChild(Exception):
    def __init__(self, node, identifier):
        self.node = node
        self.identifier = identifier

    def __str__(self):
        return f"{self.identifier} is already present in {self.node}"
