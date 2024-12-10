from abstracttree import MaxDepth

from .basenode import BaseNode
from .node import Node

__all__ = [
    "BaseNode",
    "Node",
    "TreeMixin",
    "MaxDepth",
]

__version__ = "0.8.3"

from .treemixin import TreeMixin
