"""
Logs actions using the actrack.log signal sending function
"""

from  django.utils.unittest import TestCase

import actrack
from actrack.models import Action
from actrack.compat import get_user_model

from .app.models import Project


class CreationTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create()
        self.project = Project.objects.create()

    def test_send_signal(self):
        actrack.log(self.user, verb='tests', related=self.project)
        self.assertEqual(len(Action.objects.all()), 1)
        created_action = Action.objects.all()[0]
        self.assertEqual(list(created_action.related.all()), [self.project])
        self.assertEqual(created_action.verb, 'tests')
        self.assertEqual(created_action.actor, self.user)
