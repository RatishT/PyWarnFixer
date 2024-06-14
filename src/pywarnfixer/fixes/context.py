from enum import Enum


class Context(Enum):
    """
    Enum representing the context in which a pylint warning fix is applied.
    """
    LINE = "line"
    METHOD = "method"
    CLASS = "class"
    FILE = "file"
    MODULE = "module"
    PROJECT = "project"
