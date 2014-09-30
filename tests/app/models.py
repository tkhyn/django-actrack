from django.db import models
from actrack import track


class Base(models.Model):

    name = models.CharField(max_length=255)

    class Meta:
        abstract = True


@track
class Project(Base):
    pass


@track
class Task(Base):
    parent = models.ForeignKey(Project)
