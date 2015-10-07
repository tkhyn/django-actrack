from .version import __version__, __version_info__

from .decorators import connect
from .signals import log
from .actions import track, untrack

default_app_config = 'actrack.apps.ActrackConfig'
