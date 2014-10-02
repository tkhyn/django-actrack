from .gfk import add_relation
from .models import Action
from .descriptors import ActrackDescriptor
from .managers import ActionManager, TrackerManager
from .settings import ACTIONS_ATTR, TRACKERS_ATTR


def connect(cls):
    """
    Model decorator to create relationships between the given model class
    and the Action model
    """

    # adding generic relation with actor GFK
    rel_name = 'actions_as_actor'
    add_relation(cls, Action.actor, rel_name,
                 'actions_with_%(class)s_as_actor')
    # we want a hidden relation, so the attribute should not be set
    delattr(cls, rel_name)

    # adding hidden gm2m relations
    Action.changed.add_relation(cls)
    Action.related.add_relation(cls)

    # adding actions and trackers managers
    for name, mngr in ((ACTIONS_ATTR, ActionManager),
                       (TRACKERS_ATTR, TrackerManager)):
        ActrackDescriptor(mngr).add_to_model(cls, name)

    return cls
