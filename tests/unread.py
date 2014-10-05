from actrack import log, track
from actrack.compat import get_user_model
from actrack.models import Action

from ._base import TestCase
from .app.models import Project


class UnreadTests(TestCase):

    def setUp(self):
        self.user0 = get_user_model().objects.create(username='user0')
        self.user1 = get_user_model().objects.create(username='user1')

        self.project = Project.objects.create()

        track(self.user0, self.user1, actor_only=True)

        log(self.user1, 'created', targets=self.project)
        log(self.user1, 'validated', targets=self.project)

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
