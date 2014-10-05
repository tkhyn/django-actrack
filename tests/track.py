from ._base import TestCase

import actrack
from actrack.models import Action, Tracker

from .app.models import Project


class TrackTests(TestCase):

    def setUp(self):
        self.user = self.user_model.objects.create(username='user')
        self.project = Project.objects.create()

    def test_track(self):
        # tracking all verbs on project
        actrack.track(self.user, self.project)
        trackers = Tracker.objects.all()
        self.assertEqual(len(trackers), 1)
        tracker = trackers[0]
        self.assertEqual(tracker.user, self.user)
        self.assertEqual(tracker.tracked, self.project)
        self.assertSetEqual(tracker.verbs, set())

    def test_track_verbs(self):
        # tracking verb 'modified' on project
        actrack.track(self.user, self.project, verbs='modified')
        self.assertSetEqual(Tracker.objects.all()[0].verbs, set(['modified']))

    def test_track_log(self):
        # tracking all verbs on project, logging the tracking event
        actrack.track(self.user, self.project, log=True)
        actions = Action.objects.all()
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action.actor, self.user)
        self.assertSetEqual(set(action.targets.all()), set([self.project]))
        self.assertEqual(action.verb, 'started tracking')

    def test_track_model(self):
        actrack.track(self.user, Project, verbs='created')
        tracker = Tracker.objects.all()[0]
        self.assertEqual(tracker.tracked, Project)
