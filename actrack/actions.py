from django.utils.timezone import now
from django.utils import six

from .models import Action
from .gfk import get_content_type


def create_action(verb, **kwargs):
    """
    Creates an action
    """

    kwargs.pop('signal', None)
    actor = kwargs.pop('sender')

    try:
        # Try and retrieve untranslated verb if applicable
        verb = verb._proxy__args[0]
    except (AttributeError, IndexError):
        pass

    action = Action.objects.create(
        actor_ct=get_content_type(actor),
        actor_pk=actor._get_pk_val(),
        verb=six.text_type(verb),
        timestamp=kwargs.pop('timestamp', now())
    )

    for attr in ('changed', 'related'):
        l = kwargs.pop(attr, None)
        if l is None:
            continue  # nothing to do
        elif not isinstance(l, (tuple, list, set)):
            l = [l]  # convert to a sequence
        setattr(action, attr, l)

    return action
