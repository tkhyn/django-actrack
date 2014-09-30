from django.utils.unittest import TestCase

import actrack
from actrack.models import Action

from .app.models import Base, Project, Task


class RegistrationTestCases(TestCase):

    def test_track_abstract_model(self):
        """
        It is not allowed to connect abstract models
        """
        with self.assertRaises(AssertionError):
            actrack.connect(Base)

    def test_model_relations(self):
        """
        Check that the relations are correctly setup
        """
        for m in (Project, Task):
            self.assertIs(m.actions_as_related.related.model, Action)
            self.assertIs(m.actions_as_changed.related.model, Action)
            self.assertIs(m.actions_as_actor.field.related.parent_model,
                          Action)
