from .version import __version__, __version_info__

default_app_config = 'actrack.apps.ActrackConfig'

from .decorators import connect
from .signals import log
from .actions import track, untrack
