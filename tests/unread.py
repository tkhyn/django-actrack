import time
from datetime import timedelta

from actrack import track
from actrack.models import Action, Tracker, TempTracker, now
from actrack.gfk import get_content_type

from ._base import TestCase
from .app.models import Project, Task


class UnreadTests(TestCase):

    def setUp(self):
        self.user0 = self.user_model.objects.create(username='user0')
        self.user1 = self.user_model.objects.create(username='user1')

        self.project = Project.objects.create()

        track(self.user0, self.user1, actor_only=True)

        self.log(self.user1, 'created', targets=self.project)
        self.log(self.user1, 'validated', targets=self.project)
        self.save_queue()

        # wait a little bit before retrieving actions
        time.sleep(0.01)

    def test_is_unread_for(self):
        action = self.user0.actions.feed()[0]
        self.assertTrue(action.is_unread_for(self.user0))
        self.assertFalse(action.is_unread_for(self.user1))

    def test_mark_read_for(self):
        action = self.user0.actions.feed()[0]
        action.mark_read_for(self.user0)
        self.assertFalse(action.is_unread_for(self.user0))

    def test_render(self):
        action = self.user0.actions.feed()[0]
        action.render(self.user0)
        self.assertFalse(action.is_unread_for(self.user0))

    def test_bulk_is_unread_for(self):
        self.user0.actions.feed()[0].mark_read_for(self.user0)
        self.assertListEqual(
            Action.bulk_is_unread_for(self.user0, self.user0.actions.feed()),
            [False, True]
        )

    def test_bulk_mark_read_for(self):
        Action.bulk_mark_read_for(self.user0, self.user0.actions.feed())
        self.assertListEqual(
            Action.bulk_is_unread_for(self.user0, self.user0.actions.feed()),
            [False, False]
        )

    def test_bulk_render(self):
        # as AUTO_READ setting is true, rendering actions marks them as read
        # automatically
        Action.bulk_render(self.user0.actions.feed(), self.user0)
        self.assertListEqual(
            Action.bulk_is_unread_for(self.user0, self.user0.actions.feed()),
            [False, False]
        )


class MultipleUnreadTests(TestCase):
    """
    Tests to make sure that actions are not marked as unread multiple times
    when they are tracked by different trackers
    """

    def setUp(self):
        self.user0 = self.user_model.objects.create(username='user0')
        self.user1 = self.user_model.objects.create(username='user1')

        self.project = Project.objects.create(name='project')
        self.task = Task.objects.create(project=self.project, name='task')

        track(self.user1, self.project, actor_only=False)
        track(self.user1, self.task, actor_only=False)

        self.log(self.user0, 'created', targets=self.task, related=self.project,
                 commit=True)

        # wait a little bit before retrieving actions
        time.sleep(0.01)

    def test_not_unread_twice(self):

        action = Action.objects.all()[0]

        t_proj = Tracker.objects.get(tracked_ct=get_content_type(Project))
        t_proj.update_unread()

        self.assertTrue(action.is_unread_for(self.user1))

        action.mark_read_for(self.user1)

        # check unread actions for second tracker
        t_task = Tracker.objects.get(tracked_ct=get_content_type(Task))
        t_task.update_unread()

        # the action should not be marked as unread a second time as it has
        # already been fetched through the first tracker
        self.assertFalse(action.is_unread_for(self.user1))

    def test_temp_tracker(self):
        """
        Same as above but with a temporary tracker
        """

        action = Action.objects.all()[0]

        t_proj = Tracker.objects.get(tracked_ct=get_content_type(Project))
        t_proj.update_unread()

        self.assertTrue(action.is_unread_for(self.user1))

        action.mark_read_for(self.user1)

        # check unread actions for an antedated temporary tracker
        t_task = TempTracker(self.user1, self.task, actor_only=False,
                             last_updated=now() - timedelta(0, 1))
        t_task.update_unread()

        # the action should not be marked as unread a second time as it has
        # already been fetched through the first tracker
        self.assertFalse(action.is_unread_for(self.user1))

    def test_temp_tracker_reverse(self):
        """
        Same as above but ... reversed
        """

        action = Action.objects.all()[0]

        # check unread actions for an antedated temporary tracker
        t_task = TempTracker(self.user1, self.task, actor_only=False,
                             last_updated=now() - timedelta(0, 1))
        t_task.update_unread()

        self.assertTrue(action.is_unread_for(self.user1))

        action.mark_read_for(self.user1)

        # check unread actions for the database tracker
        t_proj = Tracker.objects.get(tracked_ct=get_content_type(Project))
        t_proj.update_unread()

        # the action should not be marked as unread a second time as it has
        # already been fetched through the first tracker
        self.assertFalse(action.is_unread_for(self.user1))
