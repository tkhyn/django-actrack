from django.utils.timezone import now
from django.utils import six
from django.utils.translation import ugettext as _
from django.db.models import Q

from .models import Action, Tracker
from .gfk import get_content_type
from .signals import log as log_action
from .helpers import to_set


def create_action(verb, **kwargs):
    """
    Creates an action
    """

    try:
        # Try and retrieve untranslated verb if applicable
        verb = verb._proxy__args[0]
    except (AttributeError, IndexError):
        pass

    # set 'normal' fields
    actor = kwargs.pop('sender')
    action = Action.objects.create(
        actor_ct=get_content_type(actor),
        actor_pk=actor._get_pk_val(),
        verb=six.text_type(verb),
        timestamp=kwargs.pop('timestamp', now())
    )

    # set many-to-many fields
    for attr in ('changed', 'related'):
        l = kwargs.pop(attr, None)
        if l is None:
            continue  # nothing to do
        elif not isinstance(l, (tuple, list, set)):
            l = [l]  # convert to a sequence
        setattr(action, attr, l)

    return action


def track(user, to_track, verbs=None, actor_only=True, log=False):
    """
    Enables a user to track objects or change his tracking options for these
    objects

    :param to_track: the object(s) to track
    :param verbs: the verbs to track. None means 'track all verbs'.
    :param actor_only: should we track actions only when the object is the
                       actor?
    :param log: should an action be logged if a tracker is created?
    """

    # convert to_track and verbs to sets
    to_track = to_set(to_track)
    verbs = to_set(verbs)

    # create query to retrieve matching trackers
    q = Q()
    for obj in to_track:
        q = q | Q(tracked_ct=get_content_type(obj),
                  tracked_pk=obj.pk)
    q = q & Q(user=user)

    # fetch matching trackers
    trackers = list(Tracker.objects.filter(q)
                                   .prefetch_related('tracked'))
    tracked_objs = []

    # modify existing matching trackers if needed
    for tracker in trackers:
        if tracker.verbs != verbs:
            tracker.verbs = verbs
            tracker.save()
        tracked_objs.append(tracker.tracked)

    # create trackers to untracked objects
    untracked_objs = to_track.difference(tracked_objs)
    for obj in untracked_objs:
        trackers.append(Tracker.objects.create(user=user,
                                               tracked=obj,
                                               verbs=verbs,
                                               actor_only=actor_only))
    if log and untracked_objs:
        log_action(user, verb=_('started tracking'), changed=untracked_objs)


def untrack(user, to_untrack, verbs=None, log=False):
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
    for obj in to_untrack:
        q = q | Q(tracked_ct=get_content_type(obj),
                  tracked_pk=obj.pk)
    q = q & Q(user=user)

    # retrieves matching trackers
    trackers = Tracker.objects.filter(q)
    if log:
        trackers = trackers.prefetch_related('tracked')

    verbs = to_set(verbs)
    untracked_objs = []
    if not len(verbs):
        # all verbs should be untracked, just mass-delete the tracker objects
        if log:
            # retrieve the untracked objects beforehand
            untracked_objs.extend(t.tracked for t in trackers.objects.all())
        trackers.delete()
    else:
        # only some verbs should be untracked
        to_untrack = []
        to_update = []
        for t in trackers:
            diff = trackers.verbs.difference(verbs)
            if not diff:
                to_untrack.append(t)
            else:
                to_update.append(t)

        if to_untrack:
            # delete trackers with no more verbs to follow
            if log:
                untracked_objs.extend(t.tracked for t in to_untrack)
            Tracker.objects.filter(id__in=set(to_untrack)).delete()
        if to_update:
            # update trackers which still have verbs to follow
            Tracker.objects.filter(id__in=set(to_untrack)).update(verbs=verbs)

    if untracked_objs:  # no need to check for log
        log_action(user, verb=_('stopped tracking'), changed=untracked_objs)
