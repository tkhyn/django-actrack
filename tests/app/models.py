import django
from django.db import models

import actrack


class Base(models.Model):

    name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


@actrack.connect
class Project(Base):
    def deleted_item_description(self):
        return 'Project %d' % id(self)


@actrack.connect
class Task(Base):
    parent = models.ForeignKey(Project)

    def deleted_item_description(self):
        return 'Task %d' % id(self)

if django.VERSION < (1, 7):
    from .apps import TestAppConfig
    TestAppConfig().ready()
