from django.utils.unittest import TestCase

from actrack import track
from actrack.models import Action

from .app.models import Base, Project, Task


class RegistrationTestCases(TestCase):

    def test_track_abstract_model(self):
        """
        It is not allowed to track abstract models
        """
        with self.assertRaises(AssertionError):
            track(Base)

    def test_model_relations(self):
        """
        Check that the relations are correctly setup
        """
        for m in (Project, Task):
            self.assertIs(m.actions_as_related.related.model, Action)
            self.assertIs(m.actions_as_changed.related.model, Action)
            self.assertIs(m.actions_as_actor.field.related.parent_model,
                          Action)
