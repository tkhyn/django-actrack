from django.conf import settings
from django.utils import six


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

PK_MAXLENGTH = 16

ACTIONS_ATTR = 'actions'
TRACKERS_ATTR = 'trackers'

TRACK_UNREAD = True
AUTO_READ = True
GROUPING_DELAY = 0

LEVELS = {
    'NULL': 0,
    'DEBUG': 10,
    'HIDDEN': 20,
    'INFO': 30,
    'WARNING': 40,
    'ERROR': 50,
}
DEFAULT_LEVEL = LEVELS['INFO']
READABLE_LEVEL = LEVELS['INFO']


# this needs to be here !!
__all__ = [a for a in globals().keys() if a.isupper()]


# overrides default settings with user settings
try:
    for _attr in __all__:
        try:
            globals()[_attr] = settings.ACTRACK[_attr]
        except KeyError:
            pass
except AttributeError:
    pass
