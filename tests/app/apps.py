from django.apps import AppConfig

import actrack
from actrack.managers.inst import get_user_model


class TestAppConfig(AppConfig):

    name = 'tests.app'

    def ready(self):

        # connects the user model
        actrack.connect(get_user_model())
