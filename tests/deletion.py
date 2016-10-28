"""
Testing deletion of linked objects
"""

import actrack
from actrack.models import Action, Tracker, DeletedItem
from actrack.gfk import get_content_type

from ._base import TestCase
from .app.models import Project, Task


class DeletionTests(TestCase):

    def setUp(self):
        User = self.user_model
        self.user0 = User.objects.create(username='user0')

        self.project = Project.objects.create()

        self.task1 = Task.objects.create(parent=self.project)
        self.task2 = Task.objects.create(parent=self.project)
        self.task3 = Task.objects.create(parent=self.project)

        actrack.track(self.user0, self.project, actor_only=False)

        self.log(self.user0, 'created', targets=self.project)
        self.log(self.user0, 'created', targets=self.task1,
                 related=self.project)
        self.log(self.user0, 'created', targets=self.task2,
                 related=self.project)
        self.log(self.user0, 'created', targets=self.task3,
                 related=self.project)
        self.save_queue()

    def test_delete_targets(self):
        description = self.task1.deleted_item_description()
        serialization = self.task1.deleted_item_serialization()

        self.task1.delete()
        self.assertEqual(DeletedItem.objects.count(), 1)

        deltgt = DeletedItem.objects.first()
        self.assertEqual(deltgt.description, description)
        self.assertEqual(deltgt.serialization, serialization)

        self.assertEqual(Action.objects.count(), 4)
        ct = get_content_type(DeletedItem)
        self.assertEqual(
            Action.objects.filter(action_targets__gm2m_ct=ct).count(), 1)

    def test_delete_related_tracked(self):
        # this will delete the tasks as well
        self.project.delete()
        self.assertEqual(DeletedItem.objects.count(), 4)

        # 1 'Project' deleted item
        self.assertEqual(DeletedItem.objects.filter(
            ctype=get_content_type(Project)).count(), 1)
        # 3 'Task' deleted items
        self.assertEqual(DeletedItem.objects.filter(
            ctype=get_content_type(Task)).count(), 3)

        # the actions are however still there
        self.assertEqual(Action.objects.count(), 4)
        ct = get_content_type(DeletedItem)
        self.assertEqual(
            Action.objects.filter(action_targets__gm2m_ct=ct).count(), 4)
        self.assertEqual(
            Action.objects.filter(action_related__gm2m_ct=ct).count(), 3)
        self.assertEqual(
            Tracker.objects.filter(tracked_ct=ct).count(), 1)

    def test_delete_actor(self):
        self.user0.delete()
        self.assertEqual(DeletedItem.objects.count(), 1)
        self.assertEqual(Action.objects.count(), 4)
        ct = get_content_type(DeletedItem)
        self.assertEqual(
            Action.objects.filter(actor_ct=ct).count(), 4)

        # the Tracker should be deleted as the user no longer exists
        self.assertEqual(
            Tracker.objects.filter(tracked_ct=ct).count(), 0)
