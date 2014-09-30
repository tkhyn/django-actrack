from .compat import AppConfig


class ActrackConfig(AppConfig):
    name = 'actrack'

    def ready(self):
        from .signals import log_action
        from .actions import create_action

        log_action.connect(create_action, dispatch_uid='actrack_action')
