"""
'Extends' an action by providing a way to add user-defined methods
"""

from importlib import import_module
from datetime import timedelta

from django.utils.translation import ugettext as _
from django.utils import six
from django.utils.timesince import timesince

from .helpers import str_enum, to_set
from .gfk import get_content_type
from .settings import DEFAULT_HANDLER, GROUPING_DELAY
from .actions_queue import thread_actions_queue


class ActionHandlerMetaclass(type):

    handler_classes = {}

    def __new__(mcs, name, bases, attrs):
        subclass = super(ActionHandlerMetaclass, mcs).__new__(mcs, name,
                                                              bases, attrs)
        if subclass.verb is not None:
            mcs.handler_classes[subclass.verb] = subclass
        return subclass

    @classmethod
    def default_handler(mcs):
        try:
            return mcs._default_handler
        except AttributeError:
            module, cls = DEFAULT_HANDLER.rsplit('.', 1)
            mcs._default_handler = getattr(import_module(module), cls)
            return mcs._default_handler

    @classmethod
    def handler_class(mcs, verb):
        try:
            return mcs.handler_classes[verb]
        except KeyError:
            pass

        try:
            return mcs._default_handler
        except AttributeError:
            module, cls = DEFAULT_HANDLER.rsplit('.', 1)
            mcs._default_handler = hdlr = getattr(import_module(module), cls)
            return hdlr

    @classmethod
    def create_handler(mcs, action):
        return mcs.handler_class(action.verb)(action)

    @property
    def queue(cls):
        return thread_actions_queue


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

    def get_context(self, **context):
        """
        Generates a default rendering context from existing data
        """
        context.update(
            action=self.action,
            data=getattr(self.action, 'data', {}),
            handler=self,
        )

        try:
            context.setdefault('unread',
                               self.action.is_unread_for(context['user']))
        except KeyError:
            # no user in context
            pass

        return context

    def render(self, context=None):

        return _('%(text)s, %(timeinfo)s') % {
            'text': self.get_text(),
            'timeinfo': self.get_timeinfo()
        }

    @classmethod
    def combine(cls, **kwargs):
        """
        Take action to combine a new action described by its kwargs with already
        queued actions (available through ``cls.queue``)
        :return: ``False`` if the action described by the kwargs should not be
        added to the queue
        """
        pass

    @classmethod
    def group(cls, **kwargs):
        """
        Determines if an action described by the kwargs should be merged with
        one of its predecessors or not. Can be overridden to customize the
        grouping behavior
        :param kwargs: contains at least a verb, actor and timestamp
        :return: ``False`` if the action described by the kwargs should not be
        added to the queue
        """

        grouping_delay = timedelta(seconds=kwargs.pop('grouping_delay',
                                                      GROUPING_DELAY))

        if not grouping_delay:
            # no grouping, just return nothing to exit and save the new action
            return

        # to avoid circular imports
        from .models import Action, GM2M_ATTRS

        gm2ms = {attr: kwargs.pop(attr, None) for attr in GM2M_ATTRS}

        actor = kwargs.pop('actor')
        verb = kwargs.pop('verb')
        kws = dict(
            actor_ct=get_content_type(actor),
            actor_pk=actor.pk,
            verb=verb
        )

        # try and retrieve recent existing action, as well as difference in
        # targets and related objects
        from_tstamp = kwargs.pop('timestamp') - grouping_delay
        for kwg in cls.queue[verb]:
            diff = [a for a in GM2M_ATTRS if kwg.get(a) != gm2ms[a]]
            if len(diff) < 2:
                # a matching action has been found, sync the diff, update the
                # data and return False
                for attr in diff:
                    kwg[attr].update(gm2ms[attr])
                try:
                    kwargs.update(kwg['data'])
                except KeyError:
                    pass
                if kwargs:
                    kwg['data'] = kwargs
                return False

        for action in Action.objects.db_manager(actor._state.db) \
                .prefetch_related(*GM2M_ATTRS) \
                .filter(timestamp__gte=from_tstamp, **kws):

            diff = [a for a in GM2M_ATTRS
                    if set(getattr(action, a).all()) != gm2ms[a]]
            if len(diff) < 2:
                # a matching action has been found, sync the diff, update the
                # data and return False
                for attr in diff:
                    setattr(action, attr,
                            gm2ms[attr].union(getattr(action, attr).all()))
                kwargs.update(action.data or {})
                if kwargs:
                    action.data = kwargs
                action.save()
                return False

        # no matching action could be found, a new action must be created,
        # None is returned
