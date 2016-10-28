from django.dispatch import Signal, receiver
from django.core.signals import request_finished

from .actions_queue import thread_actions_queue


# a signal to log an action
log_action = Signal(providing_args=['verb', 'targets', 'related', 'timestamp'])


def log(actor, verb, **kwargs):
    """
    Shortcut to log an action
    """
    kwargs['verb'] = verb
    return log_action.send(actor, **kwargs)


@receiver(request_finished)
def save_queued_actions(sender, **kwargs):
    thread_actions_queue.save()
