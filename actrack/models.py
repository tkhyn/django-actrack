try:
    from django.utils.timezone import now
except ImportError:
    from datetime.datetime import now

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from gm2m import GM2MField

from .settings import AUTH_USER_MODEL
from .fields import VerbsField
from .compat import load_app


class Action(models.Model):
    """
    Describes an action, initiated by an actor on changed objects, and that
    may be related to other objects
    """

    actor_ct = models.ForeignKey(ContentType)
    actor_pk = models.CharField(max_length=255)
    actor = generic.GenericForeignKey('actor_ct', 'actor_pk')

    # using hidden relations so that the related objects' model classes are
    # not cluttered. The reverse relations are available through the
    # RelatedModel's ``actions`` attribute (as a manager) and its methods
    changed = GM2MField(related_name='actions_as_changed+')
    related = GM2MField(related_name='actions_as_related+')

    verb = models.CharField(max_length=255)

    timestamp = models.DateTimeField(default=now)


class Tracker(models.Model):
    """
    Action tracking object, so that a user can track the actions on specific
    objects
    """

    # hidden relation (accessible using the model instance's ``tracker``
    # attribute and its methods
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='trackers+')

    tracked_ct = models.ForeignKey(ContentType)
    tracked_pk = models.CharField(max_length=255)
    tracked = generic.GenericForeignKey('tracked_ct', 'tracked_pk')

    verbs = VerbsField(max_length=1000)

    actor_only = models.BooleanField(default=True)

load_app()
