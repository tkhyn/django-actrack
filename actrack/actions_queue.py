from threading import local

from .gfk import get_content_type
from .helpers import to_set


class ThreadActionsQueue(local):
    """
    An object to store the actions that were created in this thread, actually
    during this request
    """
    def __init__(self):
        self.registry = []

    def __iter__(self):
        return iter(self.registry)

    def __len__(self):
        return len(self.registry)

    def __getitem__(self, n):
        return self.registry[n]

    def __delitem__(self, n):
        del self.registry[n]

    def add(self, handler_class, kwargs):
        self.registry.append((handler_class, kwargs))

    def save(self):
        """
        Save all actions in the queue in database
        """

        # avoids circular imports
        from .models import Action, GM2M_ATTRS

        for hdlr_class, kwargs in self.registry:
            gm2ms = {attr: to_set(kwargs.pop(attr, None))
                     for attr in GM2M_ATTRS}

            # there must be an actor and a timestamp
            actor = kwargs.pop('actor')
            # TODO: use bulk_create
            action = Action.objects.db_manager(actor._state.db).create(
                verb=kwargs.pop('verb'),
                actor_ct=get_content_type(actor),
                actor_pk=actor.pk,
                timestamp=kwargs.pop('timestamp'),
                level=kwargs.pop('level'),
                data=kwargs
            )

            for attr in GM2M_ATTRS:
                l = gm2ms[attr]
                if not isinstance(l, (tuple, list, set)):
                    l = [l]  # convert to a sequence
                setattr(action, attr,
                        set(l).union(getattr(action, attr).all()))

        self.registry = []


thread_actions_queue = ThreadActionsQueue()
