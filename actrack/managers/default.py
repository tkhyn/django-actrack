"""
Default managers (.objects) for Action and Tracker classes
"""

from django.db.models import Manager, Q


class DefaultActionManager(Manager):

    def tracked_by(self, tracker, **kwargs):
        """
        All the actions that are followed by a tracker
        """

        ct = tracker.tracked_ct_id
        pk = tracker.tracked_pk

        try:
            db = tracker._state.db
        except AttributeError:
            db = None

        q = Q(actor_ct=ct, actor_pk=pk)
        if not tracker.actor_only:
            kws_targets = dict(action_targets__gm2m_ct=ct,
                               action_targets__gm2m_pk=pk)
            kws_related = dict(action_related__gm2m_ct=ct,
                               action_related__gm2m_pk=pk)
            q = q | Q(**kws_targets) | Q(**kws_related)
        if tracker.verbs:
            q = q & Q(verb__in=tracker.verbs)

        return self.db_manager(db).filter(q, **kwargs).distinct()
