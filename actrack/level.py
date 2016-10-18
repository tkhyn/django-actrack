"""
A convenient module to access logging levels
"""

from django.utils import six

from .settings import LEVELS as _LEVELS


for _l, _v in six.iteritems(_LEVELS):
    globals()[_l] = _v

# this needs to be here !!
__all__ = [a for a in globals().keys() if not a.startswith('_')]
