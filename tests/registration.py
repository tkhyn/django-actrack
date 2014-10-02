from django.db.models import Manager

import actrack
from actrack.models import Action, Tracker
from actrack.descriptors import ActrackDescriptor

from ._base import TestCase

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
        Check that the managers and relations are correctly set up
        """
        for m in (Project, Task):
            for attr, model in (('actions', Action), ('trackers', Tracker)):
                self.assertTrue(isinstance(getattr(m, attr),
                                           ActrackDescriptor))
                self.assertTrue(issubclass(getattr(m, attr).manager_cls,
                                           Manager))
