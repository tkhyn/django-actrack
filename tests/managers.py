"""
Testing the correct behaviour of managers and managers functions
"""

import actrack

from ._base import TestCase
from .app.models import Project, Task


class ManagerTests(TestCase):

    def setUp(self):
        User = self.user_model
        self.user0 = User.objects.create(username='user0')
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')

        self.project = Project.objects.create()

        self.task1 = Task.objects.create(parent=self.project)
        self.task2 = Task.objects.create(parent=self.project)
        self.task3 = Task.objects.create(parent=self.project)

        actrack.track(self.user0, self.user1)
        actrack.track(self.user2, self.project, actor_only=False)

        actrack.log(self.user1, 'created', targets=self.project)
        actrack.log(self.user1, 'created', targets=self.task1,
                    related=self.project)


class ActionManagerTests(ManagerTests):

    def test_get_queryset(self):
        self.assertEqual(self.user0.actions.all().count(), 0)
        self.assertEqual(self.user1.actions.all().count(), 2)
        self.assertEqual(self.user2.actions.all().count(), 0)
        self.assertEqual(self.project.actions.all().count(), 2)
        self.assertEqual(self.task1.actions.all().count(), 1)
        self.assertEqual(self.task2.actions.all().count(), 0)
        self.assertEqual(self.task3.actions.all().count(), 0)

    def test_as_actor(self):
        self.assertEqual(self.user0.actions.as_actor().count(), 0)
        self.assertEqual(self.user1.actions.as_actor().count(), 2)
        self.assertEqual(self.project.actions.as_actor().count(), 0)

    def test_as_targets(self):
        self.assertEqual(self.user0.actions.as_targets().count(), 0)
        self.assertEqual(self.project.actions.as_targets().count(), 1)
        self.assertEqual(self.task1.actions.as_targets().count(), 1)
        self.assertEqual(self.task2.actions.as_targets().count(), 0)

    def test_as_related(self):
        self.assertEqual(self.user1.actions.as_related().count(), 0)
        self.assertEqual(self.project.actions.as_related().count(), 1)
        self.assertEqual(self.task1.actions.as_related().count(), 0)

    def test_feed(self):
        with self.assertRaises(TypeError):
            self.project.actions.feed()
        self.assertEqual(self.user0.actions.feed().count(), 2)
        self.assertEqual(self.user1.actions.feed().count(), 0)
        self.assertEqual(self.user1.actions.feed(include_own=True).count(), 2)
        self.assertEqual(self.user2.actions.feed().count(), 2)


class TrackerManagerTests(ManagerTests):

    def test_get_queryset(self):
        self.assertEqual(self.user0.trackers.all().count(), 1)
        self.assertEqual(self.user1.trackers.all().count(), 1)
        self.assertEqual(self.user2.trackers.all().count(), 1)
        self.assertEqual(self.project.trackers.all().count(), 1)
        self.assertEqual(self.task1.trackers.all().count(), 0)
        self.assertEqual(self.task2.trackers.all().count(), 0)
        self.assertEqual(self.task3.trackers.all().count(), 0)

    def test_tracking(self):
        self.assertEqual(self.user0.trackers.tracking().count(), 0)
        self.assertEqual(self.user1.trackers.tracking().count(), 1)
        self.assertEqual(self.project.trackers.tracking().count(), 1)
        self.assertEqual(self.task1.trackers.tracking().count(), 0)

    def test_users(self):
        self.assertSetEqual(set(self.user1.trackers.users()),
                            set([self.user0]))
        self.assertSetEqual(set(self.project.trackers.users()),
                            set([self.user2]))
        self.assertEqual(self.task2.trackers.users().count(), 0)

    def owned(self):
        with self.assertRaises(TypeError):
            self.project.trackers.owned()
        self.assertEqual(self.user0.trackers.owned().count(), 1)
        self.assertEqual(self.user1.trackers.owned().count(), 0)
        self.assertEqual(self.user2.trackers.owned().count(), 1)

    def tracked(self):
        self.assertSetEqual(set(self.user0.trackers.tracked()),
                            set([self.user1]))
        self.assertSetEqual(set(self.user2.trackers.tracked()),
                            set([self.project]))
        self.assertEqual(len(self.user1.trackers.tracked()), 0)
