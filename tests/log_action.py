"""
Logs actions using the actrack.log signal sending function
"""

from ._base import TestCase

import actrack
from actrack.models import Action

from .app.models import Project


class CreationTests(TestCase):

    def setUp(self):
        self.user = self.user_model.objects.create(username='user')
        self.project = Project.objects.create()

    def test_send_signal(self):
        actrack.log(self.user, 'tests', related=self.project)
        self.assertEqual(len(Action.objects.all()), 1)
        created_action = Action.objects.all()[0]
        self.assertEqual(list(created_action.related.all()), [self.project])
        self.assertEqual(created_action.verb, 'tests')
        self.assertEqual(created_action.actor, self.user)

    def test_data(self):
        actrack.log(self.user, 'tests', targets=self.project, my_data=0)
        created_action = Action.objects.all()[0]
        self.assertEqual(created_action.data['my_data'], 0)
