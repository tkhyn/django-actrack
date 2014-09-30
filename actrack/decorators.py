from .gfk import add_relation
from .models import Action
from .compat import get_model_name


def track(cls):
    """
    Model decorator
    """
    Action.changed.add_relation(cls)
    Action.related.add_relation(cls)

    add_relation(cls, Action.actor, 'actions_as_actor',
                 'actions_with_%s_as_actor' % get_model_name(cls))

    return cls
