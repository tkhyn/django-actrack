from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.timezone import now
from django.utils import six

from gm2m import GM2MField
from jsonfield import JSONField

from .handler import ActionHandlerMetaclass, ActionHandler
from .managers.default import DefaultActionManager
from .settings import USER_MODEL, TRACK_UNREAD, AUTO_READ, PK_MAXLENGTH, \
    DEFAULT_LEVEL, READABLE_LEVEL
from .fields import OneToOneField, VerbsField
from .gfk import ModelGFK, get_content_type


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
    targets = GM2MField(pk_maxlength=PK_MAXLENGTH,
                        related_name='actions_as_target+')
    related = GM2MField(pk_maxlength=PK_MAXLENGTH,
                        related_name='actions_as_related+')

    verb = models.CharField(max_length=255)
    level = models.PositiveSmallIntegerField(default=DEFAULT_LEVEL)
    data = JSONField(blank=True, null=True)

    timestamp = models.DateTimeField(default=now)

    # default manager
    objects = DefaultActionManager()

    class Meta:
        ordering = ('-timestamp',)

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._unread_in_cache = {}
        try:
            self.handler = \
                ActionHandlerMetaclass.handler_classes[self.verb](self)
        except KeyError:
            self.handler = ActionHandler(self)

    def _render(self, context=None):
        """
        Renders the action from a template
        """
        return self.handler.render(context)

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

    def render(self, user=None, context=None):
        """
        Renders the action, attempting to mark it as read if user is not None
        Returns a rendered string
        """
        if not context:
            context = {}
        if user:
            context['user'] = user
        else:
            user = context.get('user', None)
        if user and 'unread' not in context:
            context['unread'] = self.mark_read_for(user)
        return self._render(context)

    @classmethod
    def bulk_is_unread_for(cls, user, actions):
        """
        Does not bring any performance gains over Action.is_read method, exists
        for the sake of consistency with bulk_mark_read_for and bulk_render
        """
        unread = []
        for a in actions:
            if a.level >= READABLE_LEVEL:
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
        to_mark_read = []
        for a in actions:
            is_unread = a in unread_actions
            unread.append(is_unread)
            if is_unread:
                to_mark_read.append(a)

        user.unread_actions.bulk_mark_read(to_mark_read, force)

        return unread

    @classmethod
    def bulk_render(cls, actions=(), user=None, context=None):
        """
        Renders an iterable actions, returning a list of rendered
        strings in the same order as ``actions``

        If ``user`` is provided, the class method will attempt to mark the
        actions as read for the user using Action.mark_read above
        """
        if not context:
            context = {}
        if user:
            context['user'] = user
        else:
            user = context.get('user', None)

        unread = context.pop('unread', None)
        if unread is None and user:
            unread = cls.bulk_mark_read_for(user, actions)
        else:
            # no need to attempt using count(), if actions is a queryset it
            # needs to be evaluated next anyway
            unread = [unread] * len(actions)

        rendered = []
        for a, urd in zip(actions, unread):
            rendered.append(a._render(dict(context, unread=urd)))
        return rendered


class UnreadTracker(models.Model):
    """
    A model to keep track of unread actions for each user
    """

    user = OneToOneField(USER_MODEL, related_name='unread_actions')

    unread_actions = models.ManyToManyField(Action, related_name='unread_in')

    def all(self):
        return self.unread_actions.all()

    def mark_unread(self, *actions):
        self.unread_actions.add(*actions)
        return True

    def mark_read(self, action, force=False):
        if AUTO_READ or force:
            self.unread_actions.remove(action)
            return True
        return False

    def bulk_mark_read(self, actions, force=False):
        if AUTO_READ or force:
            self.unread_actions.remove(*actions)
            return True
        return False


class TrackerBase(object):
    """
    A base class for Tracker and TempTracker
    """

    def matches(self, action):
        """
        Returns true if an action is to be tracked by the Tracker object
        """
        if action.actor == self.tracked:
            return True
        if not self.actor_only and (self.tracked in action.targets.all()
                                    or self.tracked in action.related.all()):
            return True
        return False

    def update_unread(self, already_fetched=()):
        """
        Retrieves the actions having occurred after the last time the tracker
        was updated and mark them as unread (bulk-add to unread_actions).
        """

        if not TRACK_UNREAD:
            return set()

        # fetch other trackers to check if the matching actions have been
        # read through another tracker
        trackers = Tracker.objects.exclude(pk=self.pk) \
                                  .filter(user=self.user,
                                          last_updated__gt=self.last_updated)

        # get actions that occurred since the last time the tracker
        # was updated
        last_actions = set(Action.objects.tracked_by(self) \
                                 .filter(timestamp__gte=self.last_updated,
                                         level__gte=READABLE_LEVEL))

        fetched_elsewhere = set(already_fetched)
        for action in last_actions:
            for t in trackers:
                to_mark_as_fetched_in_t = set()
                if t.matches(action):
                    if action.timestamp < t.last_updated:
                        # the action has already been fetched by t, so it is
                        # not necessary to mark it as unread now
                        fetched_elsewhere.add(action)
                    else:
                        # it's the first time the action is fetched, so we
                        # mark it as fetched in the tracker t
                        to_mark_as_fetched_in_t.add(action)
                # mark actions as fetched in tracker t
                t.fetched_elsewhere.add(*to_mark_as_fetched_in_t)

        last_actions.difference_update(fetched_elsewhere)

        self.user.unread_actions.mark_unread(*last_actions)

        self.last_updated = now()
        self.save()

        return last_actions


class Tracker(models.Model, TrackerBase):
    """
    Action tracking object, so that a user can track the actions on specific
    objects
    """

    # hidden relation (made accessible through the model instance's 'tracker'
    # attribute and its methods)
    user = models.ForeignKey(USER_MODEL, related_name='trackers+')

    tracked_ct = models.ForeignKey(ContentType)
    # tracked_pk supports null value to refer to the model class only
    tracked_pk = models.CharField(null=True, max_length=255)
    tracked = ModelGFK('tracked_ct', 'tracked_pk')

    verbs = VerbsField(max_length=1000)

    actor_only = models.BooleanField(default=True)

    # unread Actions tracking
    last_updated = models.DateTimeField(default=now)
    fetched_elsewhere = models.ManyToManyField(Action, related_name='fetched+')

    def update_unread(self):
        last_actions = super(Tracker, self) \
                       .update_unread(self.fetched_elsewhere.all())
        self.fetched_elsewhere.clear()
        return last_actions


class TempTracker(TrackerBase):
    """
    A tracker that is designed to be used 'on the fly' and is not saved in
    the database
    Typically used to retrieve all actions regarding an object, without needing
    to specifically track this object
    """

    # we need to set a pk attribute as the update_unread needs it
    # we use 0 as it is not a django model
    pk = 0

    def __init__(self, user, tracked, verbs=(), actor_only=True,
                 last_updated=None):
        self.user = user
        self.tracked = tracked
        self.verbs = verbs
        self.actor_only = actor_only
        self.last_updated = last_updated or now()

        self.tracked_ct = get_content_type(tracked)
        self.tracked_ct_id = self.tracked_ct.pk
        self.tracked_pk = tracked.pk

    def save(self):
        # mocks django model, do nothing
        pass


class DeletedItem(models.Model):
    """
    A model to keep track of objects that have been deleted but that still
    need to be linked by Action instances
    """

    ctype = models.ForeignKey(ContentType)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description
