from .compat import AppConfig

from gm2m.signals import deleting


class ActrackConfig(AppConfig):
    name = 'actrack'

    def ready(self):
        from .signals import log_action
        from .actions import create_action
        from .deletion import handle_deleted_items

        log_action.connect(create_action, dispatch_uid='actrack_action')
        deleting.connect(handle_deleted_items,
                         dispatch_uid='actrack_mkdeleted')
