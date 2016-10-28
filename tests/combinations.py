from actrack.models import Action

from ._base import TestCase


class CombiningTests(TestCase):

    def setUp(self):
        self.user0 = self.user_model.objects.create(username='user0')

    def test_combination(self, **kw):
        self.log(self.user0, 'my_included_action')
        self.log(self.user0, 'my_all_inclusive_action')
        self.log(self.user0, 'my_included_action')
        self.save_queue()

        self.assertEqual(Action.objects.count(), 1)
