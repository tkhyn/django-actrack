from django.apps import AppConfig
from django.core.signals import request_finished

from gm2m.signals import deleting


class ActrackConfig(AppConfig):
    name = 'actrack'

    def ready(self):
        from .signals import log_action, save_queue
        from .actions import create_action, save_queue as do_save_queue
        from .deletion import handle_deleted_items

        log_action.connect(create_action, dispatch_uid='actrack_action')
        deleting.connect(handle_deleted_items,
                         dispatch_uid='actrack_mkdeleted')

        save_queue.connect(do_save_queue, dispatch_uid='actrack_save')
        request_finished.connect(do_save_queue,
                                 dispatch_uid='actrack_save_on_exit')
