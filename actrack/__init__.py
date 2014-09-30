from .version import __version__, __version_info__

default_app_config = 'actrack.apps.ActrackConfig'

from .decorators import track
from .signals import log
