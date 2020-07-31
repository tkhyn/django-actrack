.. _advanced:

Advanced features
=================


The :ref:`quick-start` section showed you how to log, track and retrieve
activity related to given instances.

This section provides more details on ``django-actrack`` basic workflow and
presents some of its more advanced features.


Action creation parameters
--------------------------

Check the API documentation for :ref:`actrack.log <actrack.log>` to learn more
about the additional parameters that it can accept.


.. _ActionHandler:

Action handlers
---------------

For each action you are using in your code, you can create a subclass of
``actrack.ActionHandler`` with a corresponding ``verb`` class attribute that
will be related to this action. An instance of this handler class will be
attached to any ``Action`` object that is created or retrieved, as the
``handler`` attribute::

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
      Called when you call ``render`` on an Action instance. See Rendering_

   get_text
      Returns the text associated to the action

   get_timeinfo
      Returns the time info of the action

   get_context
      Returns a default rendering context for the action, should you need it
      for template rendering

   combine(kwargs) [classmethod]
      See Combination_

   group(newer_kw, older_kw) [classmethod]
      See Grouping_

See the `actrack.handler module`_ for default implementations.

You can of course override any of the above methods in the ``ActionHandler``
subclasses if you need to customise how certain actions should be rendered or
combined.


Combination
-----------

Sometimes, actions should be combined. Either because 2 same actions with
different arguments occurred at the same time, because two actions are
redundant and should be merged, or for whatever app-dependant reason.

Only actions with the same actor and targets can be combined.

`Action handlers`_ can define custom ``combine_with_[verb]`` methods that
determine what to do when a ``verb`` action is already in the queue. The method
takes the keyword arguments that would be passed to the 'Action'
constructor, and can make use of ``self.queue``, a registry of all the
previously added keyword arguments in this request. When this method returns
``True``, the currently logged action is discarded. In this case, it is the
responsibility of ``combine_with_[verb]`` to amend the action to which the
discarded action is combined.

Note that the combination occurs when the action is logged. If an action is
combined / discarded, it is not placed into the queue. The queue is saved to
the database when a request finishes, after Grouping_ takes place.


.. _grouping:

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
overriding the ``group`` method in the ``ActionHandler`` subclass relative to
the relevant action.

Grouping only occurs when the action queue is saved.


.. _deleted-items:

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

When the ``TRACK_UNREAD`` :ref:`setting <settings>` is set to ``True``,
``django-actrack`` can make the distinction between read and unread actions.

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


.. _`actrack.handler module`: https://github.com/tkhyn/django-actrack/src/release/actrack/handler.py
