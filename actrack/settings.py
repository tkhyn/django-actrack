from django.conf import settings
from django.utils import six


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
ACTIONS_ATTR = 'actions'
TRACKERS_ATTR = 'trackers'
TRACK_UNREAD = True
AUTO_READ = True
GROUPING_DELAY = 0
PK_MAXLENGTH = 16
TEMPLATES = [
    'actrack/%(verb)s/action.html',
    'actrack/action.html',
]

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
