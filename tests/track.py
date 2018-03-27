import warnings

from ._base import TestCase

import actrack
from actrack.models import Action, Tracker, TempTracker

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
        self.assertSetEqual(Tracker.objects.all()[0].verbs, {'modified'})

    def test_track_log(self):
        # tracking all verbs on project, logging the tracking event
        actrack.track(self.user, self.project, log=True)
        self.save_queue()

        actions = Action.objects.all()
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action.actor, self.user)
        self.assertSetEqual(set(action.targets.all()), {self.project})
        self.assertEqual(action.verb, 'started tracking')

    def test_track_model(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actrack.track(self.user, Project, verbs='created')
        tracker = Tracker.objects.all()[0]
        self.assertEqual(tracker.tracked, Project)


class TempTrackTests(TestCase):

    def setUp(self):
        self.user = self.user_model.objects.create(username='user')
        self.project = Project.objects.create()
        # creates temporary tracker for project
        self.tracker = TempTracker(self.user, self.project)

    def test_temp_track(self):
        self.log(self.project, 'started', commit=True)
        self.assertListEqual(list(Action.objects.tracked_by(self.tracker)),
                             list(Action.objects.all()))
