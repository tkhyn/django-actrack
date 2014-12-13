django-actrack
==============

|copyright| 2014 Thomas Khyn

An activity tracker for django.


Features
--------

- Actions are defined by an actor, a verb and optional targets and related
  objects (yes, from any model and as many as you want, thanks to django-gm2m)
  as well as additional data
- Convenient accessors from any model instance (like ``userX.actions.feed()``)
- Users can track objects for specific action types (verbs)
- Deleted items do not disappear from the activity tracker
- Unread/read status actions
- Actions grouping when similar actions occur close to one another
- Works with Django 1.4 to 1.6 and matching Python versions (2.6 to 3.4)

Installation
------------

As straightforward as it can be, using pip::

   pip install django-actrack

You then need to add ``'actrack'`` in your settings module's
``INSTALLED_APPS``.

Quick start
-----------

Well, to track actions, the first things we need are ... actions.
Let's generate some. We use ``actrack.log``::

   import actrack

   actrack.log(user, 'had_lunch')

``user`` could as welle be any instance of any model, it does not have to be a
user. Could be a train, for example.

You can also provide targets and related objects::

   actrack.log(train, 'left_station', targets=[from], related=[destination])

Or any relevant data::

   actrack.log(train, 'arrived', time=now())

Great. We've generated a few actions, it's now time to retrieve them.
``django-actrack`` uses trackers for that purpose. To create a tracker, use
``actrack.track``::

   actrack.track(user, train)

This creates a tracker entry in the database that will be used to retrieve
every matching action. In that case, anything that concerns ``train``.
``train`` could have been any other instance of any other model, or even a
model class itself to follow any instance of that model, but ``user`` must be
an instance of the ``USER_MODEL`` specified in the Settings_ (which defaults
to the ``AUTH_USER_MODEL`` in Django 1.6+ or ``auth.User`` in previous Django
versions).

To retrieve every action matching this tracker, ``django-actrack`` provides
convenient accessors, provided you have connected the model to it beforehand::

   @actrack.connect
   class MyModel(models.Models):
      ...

However, it is not always possible to use this decorator in this manner. The
most common example is ``auth.User``. We therefore use ``connect`` as a simple
function, somewhere in our app so that it is executed when it is loaded::

   actrack.connect(UserModel)

This will expose two attributes ``actions`` and ``trackers`` for every instance
of the model. We'll be able to do::

   for action in user.actions.feed():
      # iterate over all the actions user is tracking


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

can_group
   If ``False``, prevents this action from being grouped with a previous recent
   action. See Grouping_ below. Defaults to ``True``.


actrack.track
.............

``actrack.track`` can be used either to create a tracker or modify an existing
one. It can track model instances but also model classes.

log
   If set to ``True``, the function will log an action with the verb
   'started tracking'. Defaults to ``False``

actor_only
   Will track actions only when the provided tracked object is the actor of
   an action. Default to ``False``.

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


Grouping
--------

When the same action is repeated over a number of objects or on the same
object, it is useless to show very similar actions a number of times.

``django-actrack`` can detect if an action that is being logged is similar to
recent actions and, if it finds one, it amends it instead of creating a new
one.

The definition of 'recent' can be changed by the ``GROUPING_DELAY`` setting, in
seconds. Individually, it is possible to disable or enable action grouping when
calling ``actrack.log`` using the ``can_group`` argument.


Deleted items
-------------

Django > 1.6 only.

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
method. It looks for templates using paths defined in the ``TEMPLATES``
setting_.

The context variables provided in the template are the ones provided as
``data`` when creating the action, with the addition of ``user`` (the user for
which the action is rendered) and ``unread``.


Settings
--------

The settings must be stored in your Django project's ``settings`` module, as
a dictionary name ``ACTRACK``. This dictionary may contain the following items:

USER_MODEL
   The user model that should be used for the owners of the tracker instances.
   Defaults to Django's ``AUTH_USER_MODEL`` (>=1.6) or ``auth.User`` (<1.6)

ACTIONS_ATTR
   The name of the accessor for actions, that can be changed in case it clashes
   with one of your models' fields. Defaults to ``'actions'``

TRACKERS_ATTR
   The name of the accessor for trackers, that can be changed in case it clashes
   with one of your models' fields. Defaults to ``'trackers'``

TRACK_UNREAD
   Should unread actions be tracked? Defaults to ``True``.

AUTO_READ
   Should actions be automatically marked as read when rendered? Defaults to
   ``True``.

GROUPING_DELAY
   The time in seconds after which an action cannot be merged with a more
   recent one. When set to 0, grouping is disabled. Defaults to ``0``

PK_MAXLENGTH
   The maximum length of the primary keys of the objects that will be linked
   to action (as targets or related). Defaults to ``16``.

TEMPLATES
   A list of paths where to look for action render templates. You can use
   ``%(verb)s``, which will be replaced by a normalized version of the action's
   ``verb`` attribute. Defaults to
   ``['actrack/%(verb)s/action.html','actrack/action.html']``.


.. |copyright| unicode:: 0xA9


.. _setting: Settings_
