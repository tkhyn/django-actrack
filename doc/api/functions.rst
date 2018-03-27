Functions
=========


This section lists all the functions exposed by ``django-actrack`` and documents
their keyword arguments.


.. _actrack.log:

actrack.log(actor, verb, \*\*kwargs)
....................................

Mandatory arguments:

actor
    The instance that generates the activity. Can be any instance of any model,
    does not have to be a user.

verb
    A string identifying the action. Tip: make it meaningful. The verb is used
    to retrieve a matching :ref:`ActionHandler` subclass

Optional keyword arguments:

targets
   A model instance or list of model instances being directly affected by the
   new action.

related
   A model instance or list of model instances being related to the new action.

.. note::
   Technically, the ``targets`` and ``related`` object lists are redundant and
   they could be merged. However it can be meaningful or practical to split the
   objects in two groups, hence the distinction.

timestamp
   The timestamp that should be recorded for the action. If not provided, this
   default to now.

level
   The logging level of the new action. Logging levels can especially be used
   to filter actions that can be marked as unread. See the LEVELS,
   READABLE_LEVEL and DEFAULT_LEVEL :ref:`settings`.

using
   The database to store the new action in.

grouping_delay
   If an action with the same verb has occurred within the last
   ``grouping_delay`` (in seconds), it is merged with the current one. If it
   is set to ``0``, this prevents the action from being grouped. See
   :ref:`Grouping <grouping>`. Defaults to ``GROUPING_DELAY``.

other keywords
   any other keyword will be included in the action's data. They must only
   contain serializable data.


.. _actrack.track:

actrack.track(user, to_track, \*\*kwargs)
.........................................

``actrack.track`` can be used either to create a tracker or modify an existing
one. It can track model instances but also model classes.

user
   The user who should track actions concerning ``to_track``. Must be an
   instance of the model defined by ``AUTH_USER_MODEL``

to_track
   Actions relative to this model instance will appear in the ``user``'s
   actions feed

log
   If set to ``True``, the function will log an action with the verb
   'started tracking'. Defaults to ``False``

actor_only
   Will track actions only when the provided tracked object is the actor of
   an action. Default to ``True``.

using
   The database to store the new tracker in.

verbs
   The verbs to track. Exclude any action that does not match the provide
   verbs. Defaults to any verb.


actrack.untrack(user, to_untrack, \*\*kwargs)
.............................................

Deletes a tracker object or deletes some verbs from its verbs set.

Mandatory arguments:

user
   See `actrack.track`_

to_untrack
   The model instance to untrack

Optional keyword arguments:

log
   See `actrack.track`_

verbs
   The verbs to stop tracking. If it is empty or equal to the current verbs
   set, no verb is to be tracked anymore and the tracker is deleted. Defaults
   to all verbs.

using
   See `actrack.track`_

@actrack.connect or actrack.connect(model)
..........................................

The ``actrack.connect`` decorator can be used with an optional argument:

use_del_items
   Should the model that is to be connected use the
   :ref:`deleted items <deleted-items>` feature? Defaults to ``True``.
