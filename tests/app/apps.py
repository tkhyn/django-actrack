from django.apps import AppConfig

import actrack


class TestAppConfig(AppConfig):

    name = 'tests.app'

    def ready(self):

        from . import action_handlers
        from actrack.managers.inst import get_user_model

        # connects the user model
        actrack.connect(get_user_model())
