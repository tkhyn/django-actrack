from actrack.models import Action

from ._base import TestCase
from .app.models import Project, Task


class RenderTests(TestCase):

    def setUp(self):
        self.user0 = self.user_model.objects.create(username='user0')

        self.project = Project.objects.create(name='project')
        self.task = Task.objects.create(project=self.project, name='task')

        self.log(self.user0, 'created', targets=self.task, related=self.project,
                 commit=True)

    def test_render(self):
        self.assertEqual(
            Action.objects.all()[0].render().replace('\n', ''),
            u'user0 created task in relation to project, 0\xa0minutes ago'
        )
