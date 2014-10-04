"""
Action and Tracker dynamic managers definition

They need to be initialized with an object instance
They are set as accessors when connecting a Model to the action tracker and
can be accessed via 'actions' or 'trackers' attributes on object instances
"""

from collections import defaultdict

from django.db.models import Q
from django.db import router
from django.core.exceptions import ImproperlyConfigured
from django.utils.six import iteritems, string_types

from ..models import Action, Tracker
from ..settings import TRACKERS_ATTR
from ..gfk import get_content_type
from ..compat import Manager, get_user_model


class InstActrackManager(Manager):
    """
    A manager that retrieves entries concerning one instance only
    """

    def __init__(self, instance):
        super(InstActrackManager, self).__init__()
        self.instance = instance
        self.instance_model = instance.__class__
        self._db = router.db_for_read(self.model)

        self.is_user = self.instance_model == get_user_model()

    def get_unfiltered_queryset(self):
        """
        To call when one wants a shortcut to the unfiltered queryset
        """
        return super(InstActrackManager, self).get_queryset()


class InstActionManager(InstActrackManager):
    """
    This manager retrieves Action instances that are linked to the instance
    """

    def __init__(self, instance):
        super(InstActionManager, self).__init__(instance)
        self.model = Action

    def get_queryset(self):
        """
        All the actions where the instance is the actor, or is in the changed
        or related objects
        """

        ct = get_content_type(self.instance)
        pk = self.instance.pk

        # actor
        q = Q(actor_ct=ct, actor_pk=self.instance.pk)

        # changed and related
        for a in ('changed', 'related'):
            q = q | Q(**{
                'action_%s__gm2m_ct' % a: ct,
                'action_%s__gm2m_pk' % a: pk
            })

        return super(InstActionManager, self).get_queryset().filter(q)

    def as_actor(self, **kwargs):
        """
        All the actions where instance is the actor
        """
        return self.get_unfiltered_queryset().filter(
            actor_ct=get_content_type(self.instance),
            actor_pk=self.instance.pk,
            **kwargs
        )

    def _get_relation(self, name):

        # find the relation
        for rel in getattr(Action, name).field.rel.rels:
            if rel.to == self.instance_model:
                return rel
        else:
            raise ImproperlyConfigured(
                'No relation found in model %(model)s towards the Action '
                'model. Please use the actrack.connect decorator on model '
                '%(model)s.' % {'model': self.instance_model})

    def as_changed(self, **kwargs):
        """
        All the actions where the instance is in the changed objects
        """
        rel = self._get_relation('changed')
        return rel.related_manager_cls(self.instance).filter(**kwargs)

    def as_related(self, **kwargs):
        """
        All the actions where the instance is in the related objects
        """
        rel = self._get_relation('related')
        return rel.related_manager_cls(self.instance).filter(**kwargs)

    def feed(self, include_own=False, **kwargs):
        """
        All the actions tracked by the user
        Only applicable if instance is a user object (TypeError thrown if not)
        """

        if not self.is_user:
            raise TypeError(
                'Cannot call "feed" on an object which is not a user.')

        # all the trackers owned by the user
        trackers = getattr(self.instance, TRACKERS_ATTR).owned()

        actors_by_ct = defaultdict(lambda: defaultdict(lambda: []))
        others_by_ct = defaultdict(lambda: defaultdict(lambda: []))

        if include_own:
            # if all the user's actions should be retrieved as well, pre-fill
            # actors_by_ct
            ct = get_content_type(self.instance).pk
            actors_by_ct[ct][self.instance.pk] = None
        elif not len(trackers):
            return self.none()

        for t in trackers:
            abct = actors_by_ct[t.tracked_ct_id]
            pk = t.tracked_pk
            if abct[pk] is None:
                # the pk is already marked to 'use' all verbs
                continue
            obct = others_by_ct[t.tracked_ct_id]
            if t.verbs:
                # append the verbs if any
                abct[pk].extend(t.verbs)
                if not t.actor_only:
                    obct[pk].extend(t.verbs)
            else:
                # else mark the tracked object as 'tracking all verbs'
                abct[pk] = None
                if not t.actor_only:
                    obct[pk] = None

            # mark any new message matching the tracker as unread if required
            # we do it here because it's more efficient to collect a bunch
            # of unread actions matching the tracker now than searching and
            # updating every tracker on action creation
            t.update_unread()

        # now we've got a dictionary actors_by_ct containing all the verbs to
        # be tracked, listed by content type and pks of tracked objects
        # from that we build a query to filter Action objects

        q = Q()

        # first we take care of actors
        for ct, pk_verbs in iteritems(actors_by_ct):
            for pk, verbs in iteritems(pk_verbs):
                kws = dict(actor_ct=ct, actor_pk=pk)
                if verbs:
                    kws['verb__in'] = verbs
                q = q | Q(**kws)

        # now we take care of changed and related objects
        for ct, pk_verbs in iteritems(others_by_ct):
            for pk, verbs in iteritems(pk_verbs):
                subq = Q(
                    action_changed__gm2m_ct=ct,
                    action_changed__gm2m_pk=pk
                ) | Q(
                    action_related__gm2m_ct=ct,
                    action_related__gm2m_pk=pk
                )
                if verbs:
                    subq = subq & Q(verb__in=verbs)
                q = q | subq
        return self.get_unfiltered_queryset().filter(q, **kwargs)


class InstTrackerManager(InstActrackManager):

    def __init__(self, instance):
        super(InstTrackerManager, self).__init__(instance)
        self.model = Tracker

    def get_queryset(self):
        """
        If instance is a user, keep only the trackers that concern the user
        If not, keep only the trackers that track the instance
        """

        q = Q(
            tracked_ct=get_content_type(self.instance),
            tracked_pk=self.instance.pk
        )
        if self.is_user:
            q = q | Q(user=self.instance)

        return super(InstTrackerManager, self).get_queryset().filter(q)

    def tracking(self, **kwargs):
        """
        All Tracker objects tracking the instance
        """
        return self.get_unfiltered_queryset().filter(
            tracked_ct=get_content_type(self.instance),
            tracked_pk=self.instance.pk,
            **kwargs
        )

    def users(self, **kwargs):
        """
        All the users tracking the instance
        """
        # fetch all trackers tracking the instance, get the user id and call
        # the user manager
        return get_user_model().objects.filter(
            pk__in=set(self.tracking().values_list('user_id', flat=True)),
            **kwargs
        )

    def owned(self, **kwargs):
        """
        If instance is a user, all Tracker objects tracked by the user.
        If not, TypeError
        """
        if not self.is_user:
            raise TypeError(
                'Cannot retrieve trackers owned by an object which is not a '
                'user.')

        return self.get_unfiltered_queryset().filter(user=self.instance,
                                                     **kwargs)

    def tracked(self, *models, **kwargs):
        """
        If instance is a user, returns a set of all objects tracked by the
        user. If not, TypeError

        :param models: a list of models
        """

        if not self.is_user:
            raise TypeError(
                'Cannot retrieve objects tracked by an object which is not a '
                'user.')

        verbs = kwargs.pop('verbs', [])
        if isinstance(verbs, string_types):
            verbs = [verbs]

        qs = self.owned(**kwargs) \
                 .filter(ct__in=[get_content_type(m) for m in models]) \
                 .prefetch_related('tracked')

        all_tracked = set()
        for t in qs:
            if not t.verbs or t.verbs.intersection(verbs):
                all_tracked.add(t.tracked)

        return all_tracked
