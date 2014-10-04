from django.conf import settings
from django.utils import six

_DEFAULTS = dict(
    AUTH_USER_MODEL=getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
    ACTIONS_ATTR='actions',
    TRACKERS_ATTR='trackers',
)

__all__ = list(_DEFAULTS.keys())

_SETTINGS = getattr(settings, 'ACTRACK_SETTINGS', {})

for name, value in six.iteritems(_DEFAULTS):
    globals()[name] = _SETTINGS.get(name, value)
