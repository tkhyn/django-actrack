import actrack
from actrack.models import Action

from ._base import TestCase
from .app.models import Project, Task


class GroupingTests(TestCase):

    @classmethod
    def setUpClass(cls):
        actrack.actions.GROUPING_DELAY = 60

    @classmethod
    def tearDownClass(cls):
        actrack.actions.GROUPING_DELAY = 0

    def setUp(self):
        self.user0 = self.user_model.objects.create(username='user0')

        self.project = Project.objects.create(name='project')
        self.task1 = Task.objects.create(name='task1', parent=self.project)
        self.task2 = Task.objects.create(name='task2', parent=self.project)
        self.task3 = Task.objects.create(name='task3', parent=self.project)

    def log_actions(self, **kw):
        actrack.log(self.user0, 'created', targets=self.project, **kw)
        actrack.log(self.user0, 'created', targets=self.task1,
                    related=self.project, **kw)
        actrack.log(self.user0, 'created', targets=self.task2,
                    related=self.project, **kw)
        actrack.log(self.user0, 'created', targets=self.task3,
                    related=self.project, **kw)

    def test_groups(self):
        self.log_actions()
        self.assertEqual(Action.objects.count(), 2)
        self.assertSetEqual(
            set(self.project.actions.as_related()[0].targets.all()),
            set([self.task1, self.task2, self.task3])
        )

    def test_no_groups(self):
        self.log_actions(can_group=False)
        # no grouping, we should have 4 logged actions
        self.assertEqual(Action.objects.count(), 4)
