from .gfk import add_relation
from .models import Action


def connect(cls):
    """
    Model decorator to create relationships between the given model class
    and the Action model
    """
    Action.changed.add_relation(cls)
    Action.related.add_relation(cls)

    add_relation(cls, Action.actor, 'actions_as_actor',
                 'actions_with_%(class)s_as_actor')

    return cls
