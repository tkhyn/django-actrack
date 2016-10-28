"""
Logs actions using the actrack.log signal sending function and save them
using the request_finished signal
"""

from django.core.signals import request_finished

from ._base import TestCase

import actrack
from actrack.models import Action

from .app.models import Project
from .app.action_handlers import MyActionHandler


class CreationTests(TestCase):

    def setUp(self):
        self.user = self.user_model.objects.create(username='user')
        self.project = Project.objects.create()

    def test_signals(self):
        actrack.log(self.user, 'tests', related=self.project)

        self.assertEqual(len(Action.objects.all()), 0)

        request_finished.send(None)

        self.assertEqual(len(Action.objects.all()), 1)
        created_action = Action.objects.all()[0]
        self.assertEqual(list(created_action.related.all()), [self.project])
        self.assertEqual(created_action.verb, 'tests')
        self.assertEqual(created_action.actor, self.user)

    def test_data(self):
        self.log(self.user, 'tests', targets=self.project, my_data=0,
                 commit=True)
        created_action = Action.objects.all()[0]
        self.assertEqual(created_action.data['my_data'], 0)

    def test_handler(self):
        self.log(self.user, 'my_action', commit=True)
        my_action = Action.objects.all()[0]
        self.assertTrue(isinstance(my_action.handler, MyActionHandler))
