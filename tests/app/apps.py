from django.apps import AppConfig

import actrack


class TestAppConfig(AppConfig):

    name = 'tests.app'

    def ready(self):

        from . import action_handlers
        from actrack.managers.inst import get_user_model

        # connects the user model
        User = get_user_model()

        actrack.connect(User)

        User.deleted_item_description = User.get_full_name
        User.deleted_item_serialization = \
            lambda u: {'user': [{'pk': u.pk}]}
