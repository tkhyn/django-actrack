.. _features:

Features
========


``actions`` and ``trackers`` accessors
--------------------------------------

All the accessors quoted below are Manager methods. The ``actions`` and
``trackers`` attributes return special instance-specific managers constructed
from ``instance``. All the methods - except ``trackers.tracked`` take keyword
arguments to further filter the result queryset (verbs, timestamp ...).

instance.actions.as_actor(\*\*kw)
   All the actions where instance is the actor.

instance.actions.as_target(\*\*kw)
   All the actions where instance is among the targets.

instance.actions.as_related(\*\*kw)
   All the actions where instance is among the related objects.

instance.actions.all()
   Overrides the normal ``all`` method and returns all the actions where
   instance is either the actor or in the targets or related objects. It is
   a combination of the results of the 3 above methods.

instance.actions.feed(\*\*kw)
   The most useful accessor. This will work only if instance is a user, and
   will return all the instances that match all the trackers the user is
   associated with.

instance.tracker.tracking(\*\*kw)
   All the trackers that are tracking the instance.

instance.tracker.users(\*\*kw)
   All the users who are tracking the instance (= the owners of the trackers
   tracking the instance returned by the above method).

instance.tracker.owned(\*\*kw)
   Works only if instance is a user, returns all the trackers owned by the
   instance.

instance.tracker.tracked(\*models, \*\*kw)
   Works only if instance is a user, returns all the objects (various types)
   tracked by the user. Be aware that if there are model class trackers, there
   can be model classes in the returned set.

instance.tracker.all()
   Overrides the normal ``all`` method. If instance is a user, will return a
   combination of ``instance.tracker.owned()`` and
   ``instance.tracker.tracking``. If not, it returns the same as
   ``instance.tracker.tracking``.


Advanced usage
--------------

This section lists additional keyword arguments that can be provided to
``django-actrack``'s exposed functions.

actrack.log
...........

timestamp
   The timestamp that should be recorded for the action. If not provided, this
   default to now.

grouping_delay
   If an action with the same verb has occurred within the last
   ``grouping_delay`` (in seconds), it is merged with the current one. If it
   is set to ``0``, this prevents the action from being grouped. See Grouping_
   below. Defaults to ``GROUPING_DELAY``.


actrack.track
.............

``actrack.track`` can be used either to create a tracker or modify an existing
one. It can track model instances but also model classes.

log
   If set to ``True``, the function will log an action with the verb
   'started tracking'. Defaults to ``False``

actor_only
   Will track actions only when the provided tracked object is the actor of
   an action. Default to ``True``.

verbs
   The verbs to track. Exclude any action that does not match the provide
   verbs. Defaults to any verb.


actrack.untrack
...............

Deletes a tracker object or deletes some verbs from its verbs set.

log
   Same as for ``actrack.track``

verbs
   The verbs to stop tracking. If it is empty or equal to the current verbs
   set, no verb is to be tracked anymore and the tracker is deleted. Defaults
   to all verbs.


actrack.connect
...............

The ``actrack.connect`` decorator can be used with or without arguments.

use_del_items
   Should the model that is to be connected use the `Deleted items`_ feature?
   Defaults to ``True``.


actrack.ActionHandler
.....................

For each action you are using in your code, you can create a subclass of
``ActionHandler`` with a corresponding ``verb`` class attribute that will be
related to this action. An instance of this handler class will be attached to
any ``Action`` object that is created or retrieved, as the ``handler``
attribute::

   from actrack import ActionHandler

   class MyActionHandler(ActionHandler):
      verb = 'my_action'

      def render(self, context):
         return 'I did that'

      def do_something(self):
         for t in self.action.targets.all():
            do_something_with_this_target(t)

Handlers are used to process the action. The only special methods are:

   render
      Called when you call ``render`` on an Action instance

   get_text
      Returns the text associated to the action

   get_timeinfo
      Returns the time info of the action

   get_context
      Returns a default rendering context for the action, should you need it
      for template rendering

   combine(timestamp, **kwargs) [classmethod]
      See Combination_ below

   group(timestamp, **kwargs) [classmethod]
      See Grouping_ below

See the actrack.handler module for default implementations.

You can of course add any method you wish to the ``ActionHandler`` subclasses.


Combination
-----------

Sometimes, actions should be combined. Either because 2 same actions with
different arguments occurred at the same time, because two actions are
redundant and should be merged, or for whatever app-dependant reason.

Only actions with the same actor and targets can be combined.

Action handlers can define custom ``combine_with_[verb]`` methods that
determine what to do when a ``verb`` action is already in the queue. The method
takes the keyword arguments that would be passed to the 'Action'
constructor, and can make use of ``self.queue``, a registry of all the
previously added keyword arguments in this request. When this method returns
``True``, the currently logged action is discarded. In this case, it is the
responsibility of ``combine_with_[verb]`` to amend the action to which the
discarded action is combined.

Note that the combination occurs when the action is logged. If an action is
combined / discarded, it is not placed into the queue. The queue is saved to
the database when a request finishes, after Grouping_ takes palce.


Grouping
--------

When the same action is repeated over a number of objects or on the same
object, it is useless to show very similar actions a number of times.

``django-actrack`` provides a way to check if an action that is being logged
is similar to recent actions and, if it finds one, it amends it instead of
creating a new one.

The definition of 'recent' can be changed by the ``GROUPING_DELAY`` setting, in
seconds. Individually, it is also possible to change this delay or disable
action grouping when calling ``actrack.log`` using the ``grouping_delay``
argument.

By default, an action is considered 'similar' if it has the same actor, and at
least the same `targets` or `related` objects. This can be customized by

Grouping only occurs when the action queue is saved.


Deleted items
-------------

This is a great feature of ``django-actrack``. If an object to which an action
is related (the object can be the actor, a target or related object) is
deleted, the action itself can either be deleted (if passing
``use_del_items=False`` to ``actrack.connect``) or can remain. If it remains,
its reference to the deleted item is replaced by a reference to an instance of
a special model, that stores a verbose description of the deleted item.

For example, if the ``train`` instance is deleted (retired from the railway
company's network, for example), the actions that had been generated beforehand
refering to that ``train`` will not be deleted, and one will still be able to
read when the train started and when it arrived.

To retrieve the verbose description, ``django-actrack`` first looks for a
``deleted_item_description`` method, calls it with no arguments and takes the
returned string as the description. If that fails, it will simply evaluate
the instance as a string using ``str``.

The same thing exists for serialization. By default, the ``serialization``
field of the deleted item instance is populated with ``{'pk': object.pk}``
where ``object`` is the object being deleted. The value stored in
``serialization`` can be customized on a per-instance basis using the
``deleted_item_serialization`` method.

.. warning::

    If you are logging an action involving an instance while deleting it
    (typically within a `pre_delete` or `post_delete` signal handler), you need
    to turn it into a 'deleted item' first. This can be done using the function
    `actrack.deletion.get_del_item` which takes the instance as an argument and
    returns a deleted item instance. Be careful, get_del_item creates an entry
    for a deleted item in the database, so make sure you call it only when you
    are actually deleting an instance


Read / unread actions
---------------------

When the ``TRACK_UNREAD`` setting_ is set to ``True``, ``django-actrack``
can make the distinction between read and unread actions.

When a new action is created, it is simply considered ad unread by all users.

An action's status can be retrieved using the ``Action.is_unread_for`` method,
which takes a user as sole argument.

To update this status, you may use the ``Action.mark_read_for(user, force)``
method. ``force`` will override the ``AUTO_READ`` setting.

Alternatively, if ``AUTO_READ`` is ``True``, an action can be marked as read
when it is rendered, using its ``render`` method.

There are also classmethods on ``Action`` that implement the same functions on
a sequence of actions: ``bulk_is_unread_for``, ``bulk_mark_read_for`` and
``bulk_render``. All of them take an ordered sequence of actions as first
argument and return a list of booleans for the first two and strings for the
third.


Rendering
---------

Speaking about rendering, any action can be rendered through its ``render``
method. ``Action.render`` calls the action handler's ``render`` method, that
can be overridden in subclasses of ``ActionHandler``.

The ``ActionHandler.get_context`` method generates a useful default context
dictionary from the attached action data.
