from django import test

import actrack
from actrack.managers.inst import get_user_model
from actrack.actions import save_queue

__test__ = False
__unittest = True


class TestCase(test.TestCase):

    @property
    def user_model(self):
        return get_user_model()

    def log(self, *args, **kwargs):
        commit = kwargs.pop('commit', False)
        actrack.log(*args, **kwargs)

        if commit:
            self.save_queue()

    @staticmethod
    def save_queue():
        save_queue(None)
