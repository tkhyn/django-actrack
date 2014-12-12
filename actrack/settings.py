from django.conf import settings
from django.utils import six

_DEFAULTS = dict(
    USER_MODEL=getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
    ACTIONS_ATTR='actions',
    TRACKERS_ATTR='trackers',
    TRACK_UNREAD=True,
    AUTO_READ=True,
    GROUPING_DELAY=0,
    TEMPLATES=[
        'actrack/%(verb)s/action.html',
        'actrack/action.html',
    ],
)

__all__ = list(_DEFAULTS.keys())

_SETTINGS = getattr(settings, 'ACTRACK', {})

for name, value in six.iteritems(_DEFAULTS):
    globals()[name] = _SETTINGS.get(name, value)
