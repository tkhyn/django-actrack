from collections import defaultdict

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template.base import Context
from django.utils import six

from gm2m import GM2MField

from .managers.default import DefaultActionManager
from .settings import AUTH_USER_MODEL, TRACK_UNREAD, AUTO_READ
from .fields import VerbsField
from .compat import now, load_app


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

    # default manager
    objects = DefaultActionManager()

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._unread_in_cache = {}

    def _render(self, user, context, **kwargs):
        """
        Renders the action
        """
        return str(self)

    def unread_trackers(self, user):
        """
        Cache the set of trackers for which this action is unread for the user
        """
        try:
            return self._unread_in_cache[user.pk]
        except KeyError:
            self._unread_in_cache[user.pk] = l = \
                set(self.unread_in.filter(user=user))
            return l

    def reset_unread_in_cache(self, user=None):
        if user:
            if not hasattr(self, '_unread_in_qs'):
                self._unread_in_cache = {}
            self._unread_in_cache[user.id] = \
                list(self.unread_in.filter(user=user))
        else:
            self._unread_in_cache = {}

    def is_unread_for(self, user):
        """
        Returns True if the action is unread for that user
        """
        if self.unread_trackers(user):
            return True
        return False

    def mark_read_for(self, user, force=False, commit=True):
        """
        Attempts to mark the action as read using the tracker's mark_read
        method. Returns True if the action was unread before
        To mark several actions as read, prefer the classmethod
        bulk_mark_read_for
        """
        unread = False
        for tracker in self.unread_trackers(user):
            unread = True
            tracker.mark_read((self,), force, commit)
        # update cached unread set
        self.reset_unread_in_cache(user)
        return unread

    def render(self, user=None, context=None, commit=True, **kwargs):
        """
        Renders the action, attempting to mark it as read if user is not None
        Returns a rendered string
        """

        if not user:
            user = context.get('user', None)
        if user and not 'unread' in kwargs:
            kwargs['unread'] = self.mark_read_for(user, commit=commit)
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
    def bulk_mark_read_for(cls, user, actions, force=False, commit=True):
        """
        Marks an iterable of actions as read for the given user
        It is more efficient than calling the mark_read method on each action,
        especially if many actions belong to only a few followers

        Returns a list ``l`` of booleans. If ``actions[i]`` was unread before
        the call to bulk_mark_read_for, ``l[i]`` is True
        """

        trk_dict = defaultdict(lambda: [])
        unread = []
        for a in actions:
            urd = False  # unread marker
            for t in a.unread_trackers(user):
                trk_dict[t].append(a)
                urd = True
            unread.append(urd)

        for tracker, actions in six.iteritems(trk_dict):
            tracker.mark_read(actions, force, commit)

        # update cached querysets
        for a in actions:
            a.reset_unread_in_cache(user)

        return unread

    @classmethod
    def bulk_render(cls, actions=(), user=None, context=None, commit=True,
                    **kwargs):
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
            unread = cls.bulk_mark_read_for(user, actions, commit=commit)
        else:
            # no need to attempt using count(), if actions is a queryset it
            # needs to be evaluated next anyway
            unread = [unread] * len(actions)

        rendered = []
        for a, urd in zip(actions, unread):
            rendered.append(a._render(user, context, unread=urd, **kwargs))
        return rendered


class Tracker(models.Model):
    """
    Action tracking object, so that a user can track the actions on specific
    objects
    """

    # hidden relation (made accessible through the model instance's 'tracker'
    # attribute and its methods)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='trackers+')

    tracked_ct = models.ForeignKey(ContentType)
    tracked_pk = models.CharField(max_length=255)
    tracked = generic.GenericForeignKey('tracked_ct', 'tracked_pk')

    verbs = VerbsField(max_length=1000)

    actor_only = models.BooleanField(default=True)

    # unread Actions tracking
    last_updated = models.DateTimeField(default=now)
    unread_actions = models.ManyToManyField(Action, related_name='unread_in')

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
        self.unread_actions.add(*last_actions)
        for action in last_actions:
            action.reset_unread_in_cache()

        self.last_updated = now()
        self.save()
        return self.unread_actions.all()

    def mark_read(self, actions, force=False, commit=True):
        """
        Marks an iterable of Action objects as read. This removes them from
        the unread_actions queryset

        If ``force`` is set to True, the actions will be marked as unread no
        matter the value of self.auto_read.
        """
        if force or AUTO_READ:
            # It's not a problem if some actions are not in unread_actions
            self.unread_actions.remove(*actions)
            if commit:
                self.save()


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
