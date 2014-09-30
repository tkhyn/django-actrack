"""
Misc helper function
"""


def to_set(obj):
    """
    Converts an object to a set if it isn't already
    """

    if obj is None:
        return set()

    if isinstance(obj, set):
        return obj

    if not isinstance(obj, (tuple, list)):
        obj = [obj]

    return set(obj)
