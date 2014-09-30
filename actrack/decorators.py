from .gfk import add_relation
from .models import Action


def track(cls):
    """
    Model decorator
    """
    Action.changed.add_relation(cls)
    Action.related.add_relation(cls)

    add_relation(cls, Action.actor, 'actions_as_actor',
                 'actions_with_%(class)s_as_actor')

    return cls
