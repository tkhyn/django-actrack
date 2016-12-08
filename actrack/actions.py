import warnings

from django.utils.timezone import now
from django.utils import six
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.db import router

from .models import Tracker, GM2M_ATTRS
from .handler import ActionHandlerMetaclass
from .actions_queue import thread_actions_queue
from .gfk import get_content_type, get_pk
from .signals import log as log_action
from .helpers import to_set


def create_action(verb, **kwargs):
    """
    Creates an action
    """

    # removes the 'signal' keyword in kwargs so that it is not taken into
    # account in the action's data
    kwargs.pop('signal', None)

    # the actor is the sender
    kwargs['actor'] = kwargs.pop('sender')

    # default timestamp
    kwargs.setdefault('timestamp', now())

    try:
        # Try and retrieve untranslated verb if applicable
        verb = verb._proxy__args[0]
    except (AttributeError, IndexError):
        pass
    kwargs['verb'] = six.text_type(verb)

    for attr in GM2M_ATTRS:
        kwargs[attr] = to_set(kwargs.pop(attr, None))

    handler_class = ActionHandlerMetaclass.handler_class(verb)

    kwargs.setdefault('level', handler_class.level)

    # create the action and set 'normal' fields
    data_keys = set(kwargs.keys()).difference(
        ['grouping_delay', 'verb', 'actor', 'timestamp', 'level', 'using'] +
        list(GM2M_ATTRS)
    )
    kwargs['data'] = {f: kwargs.pop(f) for f in data_keys}

    if handler_class.combine(kwargs) is True:
        # the action should not be added / saved as it has been combined or
        # with an existing one
        return

    thread_actions_queue.add(handler_class, kwargs)


def save_queue(sender=None, **kwargs):
    thread_actions_queue.save()


def track(user, to_track, log=False, **kwargs):
    """
    Enables a user to track objects or change his tracking options for these
    objects.

    :param to_track: the object(s) to track
    :param log: should an action be logged if a tracker is created?
    :param verbs (kwarg): the verbs to track. None means 'track all verbs'
    :param actor_only (kwarg): should we track actions only when the object is
                               the actor?
    """

    # convert to_track and verbs to sets
    to_track = to_set(to_track)
    kwargs['verbs'] = to_set(kwargs.get('verbs', None))

    # create query to retrieve matching trackers
    db = kwargs.pop('using', None)
    db_from_model = False
    q = Q()
    for obj in to_track:
        pk = get_pk(obj)
        q |= Q(tracked_ct=get_content_type(obj),
               tracked_pk=pk)
        if pk:
            db = obj._state.db
        elif not db:
            db = router.db_for_read(obj)
            db_from_model = True

    if db_from_model:
        warnings.warn('The database to use for the tracker has been '
            'automatically set to the default database of the model to track. '
            'You may want to provide a db alias with the "using" kwarg.',
            Warning)

    q = q & Q(user=user)

    # fetch matching trackers
    trackers = list(Tracker.objects.db_manager(db).filter(q)
                                   .prefetch_related('tracked'))
    tracked_objs = []

    # modify existing matching trackers if needed
    for tracker in trackers:
        changed = []
        for k, v in six.iteritems(kwargs):
            if getattr(tracker, k, None) != v:
                changed.append(k)
            setattr(tracker, k, v)

        if changed:
            tracker.save()

        tracked_objs.append(tracker.tracked)

    last_updated = kwargs.pop('last_updated', None)
    if last_updated is not None:
        kwargs['last_updated'] = last_updated

    # create trackers to untracked objects
    untracked_objs = to_track.difference(tracked_objs)
    for obj in untracked_objs:
        trackers.append(Tracker.objects.db_manager(db)
                                       .create(user=user,
                                               tracked=obj,
                                               **kwargs))
    if log and untracked_objs:
        log_action(user, verb=_('started tracking'), targets=untracked_objs)


def untrack(user, to_untrack, verbs=None, log=False, using=None):
    """
    Disables tracking for the objects in to_untrack for the selected verbs

    :param to_untrack: the object(s) to untrack
    :param verbs: the verbs to untrack. None or  means 'untrack all verbs'.
    :param log: should an action be logged if a tracker is deleted?
    """

    # convert to_track and verbs to sets
    to_untrack = to_set(to_untrack)
    # create query to retrieve matching tracker
    q = Q()
    db = using
    for obj in to_untrack:
        q = q | Q(tracked_ct=get_content_type(obj),
                  tracked_pk=obj.pk)
        if not db and obj.pk:
            db = obj._state.db

    if db is None:
        raise ValueError('The database to use could not be auto-detected. '
                         'Please provide a db alias with the "using" kwarg.')

    q = q & Q(user=user)

    # retrieves matching trackers
    trackers = Tracker.objects.db_manager(db).filter(q)
    if log:
        trackers = trackers.prefetch_related('tracked')

    verbs = to_set(verbs)
    untracked_objs = []
    if not len(verbs):
        # all verbs should be untracked, just mass-delete the tracker objects
        if log:
            # retrieve the untracked objects beforehand
            untracked_objs.extend(t.tracked for t in trackers)
        trackers.delete()
    else:
        # only some verbs should be untracked
        to_untrack = []
        to_update = []
        for t in trackers:
            diff = t.verbs.difference(verbs)
            if not diff:
                to_untrack.append(t)
            else:
                to_update.append(t)

        if to_untrack:
            # delete trackers with no more verbs to follow
            if log:
                untracked_objs.extend(t.tracked for t in to_untrack)
            Tracker.objects.db_manager(db).filter(id__in=set(to_untrack)) \
                                          .delete()
        if to_update:
            # update trackers which still have verbs to follow
            Tracker.objects.db_manager(db).filter(id__in=set(to_untrack)) \
                                          .update(verbs=verbs)

    if untracked_objs:  # no need to check for log
        log_action(user, verb=_('stopped tracking'), targets=untracked_objs)
