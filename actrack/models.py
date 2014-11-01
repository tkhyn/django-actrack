

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template.loader import render_to_string
from django.template.base import Context

from gm2m import GM2MField
from jsonfield import JSONField

from .managers.default import DefaultActionManager
from .settings import AUTH_USER_MODEL, TRACK_UNREAD, AUTO_READ, TEMPLATES
from .fields import OneToOneField, VerbsField
from .gfk import ModelGFK
from .compat import now, load_app


GM2M_ATTRS = ('targets', 'related')


class Action(models.Model):
    """
    Describes an action, initiated by an actor on target objects, and that
    may be related to other objects
    """

    actor_ct = models.ForeignKey(ContentType)
    actor_pk = models.CharField(max_length=255)
    actor = generic.GenericForeignKey('actor_ct', 'actor_pk')

    # using hidden relations so that the related objects' model classes are
    # not cluttered. The reverse relations are available through the
    # RelatedModel's ``actions`` attribute (as a manager) and its methods
    targets = GM2MField(related_name='actions_as_target+')
    related = GM2MField(related_name='actions_as_related+')

    verb = models.CharField(max_length=255)

    data = JSONField(blank=True, null=True)

    timestamp = models.DateTimeField(default=now)

    # default manager
    objects = DefaultActionManager()

    class Meta:
        ordering = ('-timestamp',)

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._unread_in_cache = {}

    def get_templates(self):
        norm_verb = self.verb.replace(' ', '_')
        return [t % {'verb': norm_verb} for t in TEMPLATES]

    def _render(self, user, context, **kwargs):
        """
        Renders the action from a template
        """
        dic = dict(kwargs, action=self)
        if user:
            dic['user'] = user
            if 'unread' not in dic:
                dic['unread'] = self.is_unread_for(user)

        dic.update(getattr(self, 'data', {}))

        templates = self.get_templates()
        return render_to_string(templates, dic, context)

    def is_unread_for(self, user):
        """
        Returns True if the action is unread for that user
        """
        if self in user.unread_actions.all():
            return True
        return False

    def mark_read_for(self, user, force=False):
        """
        Attempts to mark the action as read using the tracker's mark_read
        method. Returns True if the action was unread before
        To mark several actions as read, prefer the classmethod
        bulk_mark_read_for
        """
        return user.unread_actions.mark_read(self, force=force)

    def render(self, user=None, context=None, **kwargs):
        """
        Renders the action, attempting to mark it as read if user is not None
        Returns a rendered string
        """

        if not user and context:
            user = context.get('user', None)
        if user and not 'unread' in kwargs:
            kwargs['unread'] = self.mark_read_for(user)
        return self._render(user, context, **kwargs)

    @classmethod
    def bulk_is_unread_for(cls, user, actions):
        """
        Does not bring any performance gains over Action.is_read method, exists
        for the sake of consistency with bulk_mark_read_for and bulk_render
        """
        unread = []
        for a in actions:
            unread.append(a.is_unread_for(user))
        return unread

    @classmethod
    def bulk_mark_read_for(cls, user, actions, force=False):
        """
        Marks an iterable of actions as read for the given user
        It is more efficient than calling the mark_read method on each action,
        especially if many actions belong to only a few followers

        Returns a list ``l`` of booleans. If ``actions[i]`` was unread before
        the call to bulk_mark_read_for, ``l[i]`` is True
        """

        unread_actions = user.unread_actions.all()

        unread = []
        for a in actions:
            unread.append(a in unread_actions)

        user.unread_actions.bulk_mark_read(actions, force)

        return unread

    @classmethod
    def bulk_render(cls, actions=(), user=None, context=None, **kwargs):
        """
        Renders an iterable actions, returning a list of rendered
        strings in the same order as ``actions``

        If ``user`` is provided, the class method will attempt to mark the
        actions as read for the user using Action.mark_read above
        """

        if not context:
            context = Context()
        elif not user:
            user = context.get('user', None)

        unread = kwargs.pop('unread', None)
        if unread is None and user:
            unread = cls.bulk_mark_read_for(user, actions)
        else:
            # no need to attempt using count(), if actions is a queryset it
            # needs to be evaluated next anyway
            unread = [unread] * len(actions)

        rendered = []
        for a, urd in zip(actions, unread):
            rendered.append(a._render(user, context, unread=urd, **kwargs))
        return rendered


class UnreadTracker(models.Model):

    user = OneToOneField(AUTH_USER_MODEL,
                                related_name='unread_actions')

    unread_actions = models.ManyToManyField(Action, related_name='unread_in')

    def all(self):
        return self.unread_actions.all()

    def mark_unread(self, *actions):
        self.unread_actions.add(*actions)

    def mark_read(self, action, force=False):
        if AUTO_READ or force:
            self.unread_actions.remove(action)

    def bulk_mark_read(self, actions, force=False):
        if AUTO_READ or force:
            self.unread_actions.remove(*actions)


class Tracker(models.Model):
    """
    Action tracking object, so that a user can track the actions on specific
    objects
    """

    # hidden relation (made accessible through the model instance's 'tracker'
    # attribute and its methods)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='trackers+')

    tracked_ct = models.ForeignKey(ContentType)
    # tracked_pk supports null value to refer to the model class only
    tracked_pk = models.CharField(null=True, max_length=255)
    tracked = ModelGFK('tracked_ct', 'tracked_pk')

    verbs = VerbsField(max_length=1000)

    actor_only = models.BooleanField(default=True)

    # unread Actions tracking
    last_updated = models.DateTimeField(default=now)

    def update_unread(self, qs=None):
        """
        Retrieves the actions having occurred after the last time the tracker
        was updated and mark them as unread (bulk-add to unread_actions).
        """

        if not TRACK_UNREAD:
            return set()

        qs = Action.objects.tracked_by(self)

        # get actions that occurred since the last time the tracker
        # was updated, and add them to unread_actions
        last_actions = qs.filter(timestamp__gte=self.last_updated)

        self.user.unread_actions.mark_unread(*last_actions)

        self.last_updated = now()
        self.save()

        return last_actions


class DeletedItem(models.Model):
    """
    A model to keep track of objects that have been deleted but that still
    need to be linked by Action instances
    """

    ctype = models.ForeignKey(ContentType)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description


load_app()
