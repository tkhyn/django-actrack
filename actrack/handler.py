"""
'Extends' an action by providing a way to add user-defined methods
"""

from django.utils import six


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
