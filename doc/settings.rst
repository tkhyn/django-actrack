.. _setting:

Settings
========

The settings must be stored in your Django project's ``settings`` module, as
a dictionary name ``ACTRACK``. This dictionary may contain the following items:

USER_MODEL
   The user model that should be used for the owners of the tracker instances.
   Defaults to Django's ``AUTH_USER_MODEL``

ACTIONS_ATTR
   The name of the accessor for actions, that can be changed in case it clashes
   with one of your models' fields. Defaults to ``'actions'``

TRACKERS_ATTR
   The name of the accessor for trackers, that can be changed in case it clashes
   with one of your models' fields. Defaults to ``'trackers'``

DEFAULT_HANDLER
   The path to the default action handler class (used when a matching action
   handler is not found). Defaults to ``'actrack.ActionHandler'``

TRACK_UNREAD
   Should unread actions be tracked? Defaults to ``True``.

AUTO_READ
   Should actions be automatically marked as read when rendered? Defaults to
   ``True``.

GROUPING_DELAY
   The time in seconds after which an action cannot be merged with a more
   recent one. When set to ``-1``, grouping is disabled. When set to ``0``,
   grouping occurs only on unsaved actions. Defaults to ``0``

PK_MAXLENGTH
   The maximum length of the primary keys of the objects that will be linked
   to action (as targets or related). Defaults to ``16``.

LEVELS
   A dictionary of logging levels. Defaults to::

      {
         'NULL': 0,
         'DEBUG': 10,
         'HIDDEN': 20,
         'INFO': 30,
         'WARNING': 40,
         'ERROR': 50,
      }

.. note::

   The logging levels should have upper case names and their values must be
   small positive integers from 0 to 32767

   The defined logging levels can, after initialization, be accessed under the
   ``actrack.level`` module. E.g. ``actrack.level.INFO``.

DEFAULT_LEVEL
   The default level to use for logging. Defaults to ``LEVELS['INFO']``

READABLE_LEVEL
   Below that logging level (strictly), an action cannot appear as unread and
   cannot be marked as read. Defaults to ``LEVELS['INFO']``
