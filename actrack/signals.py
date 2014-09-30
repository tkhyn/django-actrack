from django.dispatch import Signal

log_action = Signal(providing_args=['verb', 'changed', 'related', 'timestamp'])
log = log_action.send
