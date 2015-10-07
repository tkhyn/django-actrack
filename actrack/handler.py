"""
'Extends' an action by providing a way to add user-defined methods
"""

from django.utils.translation import ugettext as _
from django.utils import six
from django.utils.timesince import timesince

from .helpers import str_enum


class ActionHandlerMetaclass(type):

    handler_classes = {}

    def __new__(mcs, name, bases, attrs):
        subclass = super(ActionHandlerMetaclass, mcs).__new__(mcs, name,
                                                              bases, attrs)
        if subclass.verb is not None:
            mcs.handler_classes[subclass.verb] = subclass
        return subclass


class ActionHandler(six.with_metaclass(ActionHandlerMetaclass)):

    verb = None

    def __init__(self, action):
        self.action = action

    def get_text(self):
        a = self.action
        ctxt = {
            'actor': str(a.actor),
            'verb': a.verb,
            'targets': str_enum(a.targets.all()),
            'related': str_enum(a.related.all())
        }
        if ctxt['related']:
            return _('%(actor)s %(verb)s %(targets)s '
                     'in relation to %(related)s') % ctxt
        else:
            return _('%(actor)s %(verb)s %(targets)s') % ctxt

    def get_timeinfo(self):
        return _('%(time)s ago') % {'time': timesince(self.action.timestamp)}

    def get_context(self, context=None):
        """
        Generates a default rendering context from existing data
        """
        context = dict(
            context or {},
            action=self.action,
            data=getattr(self.action, 'data', {}),
        )

        user = context.get('user', None)
        if user and 'unread' not in context:
            context['unread'] = self.action.is_unread_for(context['user'])

        return context

    def render(self, context=None):

        return _('%(text)s, %(timeinfo)s') % {
            'text': self.get_text(),
            'timeinfo': self.get_timeinfo()
        }
