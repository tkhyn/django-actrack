from django import test

from actrack.managers.inst import get_user_model

__test__ = False
__unittest = True


class TestCase(test.TestCase):

    @property
    def user_model(self):
        return get_user_model()
