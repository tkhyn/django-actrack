from actrack import log
from actrack.models import Action

from ._base import TestCase
from .app.models import Project, Task


class RenderTests(TestCase):

    def setUp(self):
        self.user0 = self.user_model.objects.create(username='user0')

        self.project = Project.objects.create(name='project')
        self.task = Task.objects.create(parent=self.project, name='task')

        log(self.user0, 'created', targets=self.task, related=self.project)

    def test_render(self):
        self.assertEqual(
            Action.objects.all()[0].render().replace('\n', ''),
            u'<div class="action"><a href="">user0</a> created task in '
            u'relation to project 0\xa0minutes ago</div>'
        )
