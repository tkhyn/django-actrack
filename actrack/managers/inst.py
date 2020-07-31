"""
Action and Tracker dynamic managers definition

They need to be initialized with an object instance
They are set as accessors when connecting a Model to the action tracker and
can be accessed via 'actions' or 'trackers' attributes on object instances
"""

from collections import defaultdict

from django.db.models import Q, Manager
from django.db import router
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps

from ..models import Action, Tracker, GM2M_ATTRS
from ..settings import TRACKERS_ATTR, USER_MODEL, READABLE_LEVEL
from ..gfk import get_content_type


def get_user_model():
    try:
        return apps.get_model(USER_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "actrack's USER_MODEL must be of the form "
            "'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "actrack's USER_MODEL refers to model '%s' "
            "that has not been installed" % USER_MODEL)


def mk_kws(name, ct, pk, verbs=None):
    """
    Helper function to generate query dictionaries
    """
    kws = {'%s_ct' % name: ct}
    if pk is not None:
        kws['%s_pk' % name] = pk
    if verbs:
        kws['verb__in'] = verbs
    return kws


class InstActrackManager(Manager):
    """
    A manager that retrieves entries concerning one instance only
    """

    def __init__(self, instance, model):
        super(InstActrackManager, self).__init__()
        self.instance = instance
        self.instance_model = instance.__class__
        self.model = model
        try:
            self._db = instance._state.db
        except AttributeError:
            self._db = router.db_for_read(self.model)
        self.is_user = issubclass(self.instance_model, get_user_model())

    def get_queryset(self):
        """
        To call when one wants a shortcut to the unfiltered queryset
        """
        return super(InstActrackManager, self).get_queryset().distinct()


class InstActionManager(InstActrackManager):
    """
    This manager retrieves Action instances that are linked to the instance
    """

    def __init__(self, instance):
        super(InstActionManager, self).__init__(instance, Action)

    def get_queryset(self):
        """
        All the actions where the instance is the actor, or is in the targets
        or related objects
        """

        ct = get_content_type(self.instance)
        pk = self.instance.pk

        # actor
        q = Q(actor_ct=ct, actor_pk=self.instance.pk)

        # targets and related
        for a in GM2M_ATTRS:
            q = q | Q(**mk_kws('action_%s__gm2m' % a, ct, pk))

        return super(InstActionManager, self).get_queryset().filter(q)

    def as_actor(self, **kwargs):
        """
        All the actions where instance is the actor
        """
        return super(InstActionManager, self).get_queryset().filter(
            **mk_kws('actor', get_content_type(self.instance),
                     self.instance.pk))

    def _get_relation(self, name):

        # find the relation
        for rel in getattr(Action, name).field.remote_field.rels:
            if rel.model == self.instance_model:
                return rel
        else:
            raise ImproperlyConfigured(
                'No relation found in model %(model)s towards the Action '
                'model. Please use the actrack.connect decorator on model '
                '%(model)s.' % {'model': self.instance_model})

    def as_target(self, **kwargs):
        """
        All the actions where the instance is in the targets objects
        """
        rel = self._get_relation('targets')
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
        for ct, pk_verbs in actors_by_ct.items():
            for pk, verbs in pk_verbs.items():
                q = q | Q(**mk_kws('actor', ct, pk, verbs=verbs))

        # now we take care of targets and related objects
        for ct, pk_verbs in others_by_ct.items():
            for pk, verbs in pk_verbs.items():
                subq = Q(**mk_kws('action_targets__gm2m', ct, pk)) | \
                       Q(**mk_kws('action_related__gm2m', ct, pk))
                if verbs:
                    subq = subq & Q(verb__in=verbs)
                q = q | subq

        level__gte = kwargs.pop('level__gte', 0)
        kwargs['level__gte'] = max(level__gte, READABLE_LEVEL)
        return super(InstActionManager, self).get_queryset().filter(q, **kwargs)


class InstTrackerManager(InstActrackManager):

    def __init__(self, instance):
        super(InstTrackerManager, self).__init__(instance, Tracker)

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
        return super(InstTrackerManager, self).get_queryset().filter(
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

        return super(InstTrackerManager, self).get_queryset() \
            .filter(user=self.instance, **kwargs)

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
        if isinstance(verbs, str):
            verbs = [verbs]

        qs = self.owned(**kwargs) \
                 .prefetch_related('tracked')

        if models:
            qs = qs.filter(ct__in=[get_content_type(m) for m in models])

        all_tracked = set()
        for t in qs:
            if not t.verbs or t.verbs.intersection(verbs):
                all_tracked.add(t.tracked)

        return all_tracked
