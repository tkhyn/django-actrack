from django.dispatch import Signal

log_action = Signal(providing_args=['verb', 'changed', 'related', 'timestamp'])


def log(actor, verb, **kwargs):
    kwargs['verb'] = verb
    return log_action.send(actor, **kwargs)
