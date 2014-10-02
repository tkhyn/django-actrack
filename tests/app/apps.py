import actrack
from actrack.compat import AppConfig, get_user_model


class TestAppConfig(AppConfig):

    name = 'tests.app'

    def ready(self):

        # connects the user model
        actrack.connect(get_user_model())
