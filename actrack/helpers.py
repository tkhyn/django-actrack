"""
Misc helper function
"""

from django.utils.translation import ugettext as _


def to_set(obj):
    """
    Converts an object to a set if it isn't already
    """

    if obj is None:
        return set()

    if isinstance(obj, set):
        return obj

    if not hasattr(obj, '__iter__'):
        obj = [obj]

    return set(obj)


def str_enum(it):
    """
    Converts an iterable to string 'the smart way'
    """

    it = [str(o) for o in it]
    l = len(it)
    if l < 4:
        # the list of objects contains 3 items or less print all of them
        return ', '.join(it[-3:-2] + [_(' and ').join(it[-2:])])
    else:
        # the list of objects contains more than 3 items, print only the 1st
        # 2 ones and give a number
        return _('%s and %d others') % (', '.join(it[0:2]), l - 2)
