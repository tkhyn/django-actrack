Models
======


.. _Action:

Action
------

The core model of ``django-actrack``.

.. autoclass:: actrack.models.Action
    :members:
    :exclude-members: DoesNotExist, MultipleObjectsReturned

Trackers
--------

``django-actrack`` features two types of trackers. A ``Tracker`` model (which
instances are stored in the database) and a non-persistent ``TempTracker``
class which is not actually a model but instead can be used to generate
read-only queries on-the-fly.

.. autoclass:: actrack.models.Tracker
    :members:
    :inherited-members:
    :exclude-members: DoesNotExist, MultipleObjectsReturned

.. autoclass:: actrack.models.TempTracker
    :members:
    :inherited-members:

DeletedItem
-----------

See :ref:`deleted-items`.

.. autoclass:: actrack.models.DeletedItem
    :members:
    :exclude-members: DoesNotExist, MultipleObjectsReturned
