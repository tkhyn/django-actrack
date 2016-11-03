"""
'Extends' an action by providing a way to add user-defined methods
"""

from importlib import import_module
from datetime import timedelta
from copy import copy

from django.forms.models import model_to_dict
from django.utils.translation import ugettext as _
from django.utils import six
from django.utils.timesince import timesince

from .helpers import str_enum
from .gfk import get_content_type
from .settings import DEFAULT_HANDLER, GROUPING_DELAY, DEFAULT_LEVEL
from .actions_queue import thread_actions_queue


class ActionHandlerMetaclass(type):

    handler_classes = {}

    def __new__(mcs, name, bases, attrs):
        combinators = {}

        for attr, m in attrs.items():
            try:
                __, verb = attr.split('combine_with_')
            except ValueError:
                continue
            combinators[verb] = m

        try:
            group = attrs['group']
            if not isinstance(group, classmethod):
                attrs['group'] = classmethod(group)
        except KeyError:
            pass

        subclass = super(ActionHandlerMetaclass, mcs).__new__(mcs, name,
                                                              bases, attrs)

        if subclass.verb is not None:
            subclass._combinators = combinators
            mcs.handler_classes[subclass.verb] = subclass
        else:
            subclass._combinators = {}

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
    level = DEFAULT_LEVEL

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
    def _merge(cls, kws1, kws2):
        """
        Merge kws2 into kws1 (without overwriting) if they actually match
        """
        for k, v in kws2.items():
            if k == 'level':
                # level is a special case
                l1 = kws1.get(k, DEFAULT_LEVEL)
                if v > l1:
                    kws1[k] = v
                continue
            try:
                v1 = kws1[k]
                if isinstance(v1, list):
                    for it in v:
                        if it not in v1:
                            v1.append(it)
                elif isinstance(v1, set):
                    v1.update(v)
                elif isinstance(v1, dict):
                    cls._merge(v1, v)
            except KeyError:
                kws1[k] = v
        return True

    @classmethod
    def combine(cls, kwargs):
        """
        Determines if the action described by the provided kwargs should be
        committed to the db, taking into account other queued actions (available
        through ``cls.queue``)
        :return: ``True`` if the action described by the kwargs has been
        combined and should not be saved
        """

        i = len(cls.queue)
        while i and cls.queue:
            i -= 1
            handler_class, kws = cls.queue[i]

            if kws.get('actor') != kwargs.get('actor') \
            or kws.get('targets') != kwargs.get('targets'):
                continue

            try:
                # attempting to combine the action described by kwargs with
                # existing actions. If the returned value is True, we exit
                # as the kwargs-action has been merged in the kws action

                if cls._combinators[kws['verb']](cls, kwargs) is True:
                    cls._merge(kws, kwargs)
                    return True
            except KeyError:
                pass

            try:
                if handler_class._combinators[kwargs['verb']](
                handler_class, kws) is True:
                    handler_class._merge(kwargs, kws)
                    del cls.queue[i]
            except KeyError:
                pass

    @classmethod
    def group(cls, newer_kw, older_kw):
        """
        Default grouping implementation. Groups if at least the targets or
        the related objects are the same
        """
        from .models import GM2M_ATTRS
        diff = [a for a in GM2M_ATTRS if older_kw.get(a) != newer_kw.get(a)]
        if len(diff) < 2:
            # a matching action has been found, update the older_kw dict
            # without overwriting
            return True

    @classmethod
    def _group(cls, kwargs):
        """
        Determines if an action described by the kwargs should be merged with
        one of its predecessors or not. Can be overridden to customize the
        grouping behavior
        :return: ``True`` if the action described by the kwargs has been grouped
        and should not be added to the queue
        """

        kwargs['__current__'] = True
        queue = []
        for a in cls.queue:
            if not a[1].get('__current__', False):
                queue.append(a)
        kwargs.pop('__current__')

        grouping = kwargs.pop('grouping_delay', GROUPING_DELAY)

        if grouping == -1:
            # no grouping, just return nothing to exit and save the new action
            return
        else:
            grouping_delay = timedelta(seconds=grouping)

        # to avoid circular imports
        from .models import Action, GM2M_ATTRS

        kwargs = copy(kwargs)

        to_tstamp = kwargs.pop('timestamp')
        from_tstamp = to_tstamp - grouping_delay

        actor = kwargs.pop('actor')
        verb = kwargs.pop('verb')

        # try and retrieve recent existing action, as well as difference in
        # targets and related objects
        for hdlr_cls, kwg in queue:
            tstamp = kwg['timestamp']
            if kwg['verb'] != verb or kwg['actor'] != actor \
            or grouping and (tstamp < from_tstamp or tstamp > to_tstamp):
                continue

            if cls.group(kwargs, kwg):
                # do group
                cls._merge(kwg, kwargs)
                return True

        if not grouping:
            # database grouping is disabled
            return

        for action in Action.objects.db_manager(actor._state.db) \
                .prefetch_related(*GM2M_ATTRS) \
                .filter(timestamp__gte=from_tstamp,
                        timestamp__lte=to_tstamp,
                        actor_ct=get_content_type(actor),
                        actor_pk=actor.pk,
                        verb=verb):

            action_kws = {}
            for field in ['data', 'level', 'related', 'targets']:
                value = getattr(action, field)
                if field in GM2M_ATTRS:
                    value = set(value.all())
                if field == 'data':
                    action_kws.update(value)
                else:
                    action_kws[field] = value

            if cls.group(kwargs, action_kws):
                cls._merge(action_kws, kwargs)
                for k, v in action_kws.items():
                    setattr(action, k, v)
                action.save()
                return True

        # no matching action could be found, a new action must be created,
        # None is returned
