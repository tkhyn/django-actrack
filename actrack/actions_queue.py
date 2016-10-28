from threading import local
from collections import defaultdict

from .gfk import get_content_type
from .helpers import to_set


class ThreadActionsQueue(local):
    """
    An object to store the actions that were created in this thread, actually
    during this request
    """
    def __init__(self):
        self.registry = defaultdict(list)

    def __getitem__(self, item):
        return self.registry[item]

    def add(self, verb, **kwargs):
        self.registry[verb].append(kwargs)

    def save(self):
        """
        Save all actions in the queue in database
        """

        # avoids circular imports
        from .models import Action, GM2M_ATTRS

        for v, q in self.registry.items():
            for kwargs in q:
                gm2ms = {attr: to_set(kwargs.pop(attr, None))
                         for attr in GM2M_ATTRS}

                # there must be an actor and a timestamp
                actor = kwargs.pop('actor')
                action = Action.objects.db_manager(actor._state.db).create(
                    verb=v,
                    actor_ct=get_content_type(actor),
                    actor_pk=actor.pk,
                    timestamp=kwargs.pop('timestamp'),
                    data=kwargs
                )

                for attr in GM2M_ATTRS:
                    l = gm2ms[attr]
                    if not isinstance(l, (tuple, list, set)):
                        l = [l]  # convert to a sequence
                    setattr(action, attr,
                            set(l).union(getattr(action, attr).all()))

        self.registry.clear()


thread_actions_queue = ThreadActionsQueue()
