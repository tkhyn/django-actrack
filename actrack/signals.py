from django.dispatch import Signal

# a signal to log an action
log_action = Signal(providing_args=['verb', 'changed', 'related', 'timestamp'])


def log(actor, verb, **kwargs):
    """
    Shortcut to log an action
    """
    kwargs['verb'] = verb
    return log_action.send(actor, **kwargs)
