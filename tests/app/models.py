from django.db import models

import actrack


class Base(models.Model):

    name = models.CharField(max_length=255)

    class Meta:
        abstract = True


@actrack.connect
class Project(Base):
    pass


@actrack.connect
class Task(Base):
    parent = models.ForeignKey(Project)
