Managers
========


The ``actions`` manager
-----------------------

We've seen in the :ref:`quick-start` that connecting a django Model using the
``actrack.connect`` decorator exposed an ``actions`` attribute on every instance
of that Model. This ``actions`` attribute is actually a Django Manager_ that
queries :ref:`Action` instances::

   @actrack.connect
   class MyModel(models.Models):
      ...

   instance = MyModel()

   # this returns a Manager to fetch actions
   instance.actions

An ``actions`` manager has several useful methods:

``instance.actions.as_actor(\*\*kw)``
   All the actions where instance is the actor.

``instance.actions.as_target(\*\*kw)``
   All the actions where instance is among the targets.

``instance.actions.as_related(\*\*kw)``
   All the actions where instance is among the related objects.

``instance.actions.all()``
   Overrides the normal ``all`` method and returns all the actions where
   instance is either the actor or in the targets or related objects. It is
   a combination of the results of the 3 above methods.

``instance.actions.feed(\*\*kw)``
   The most useful accessor. This will work only if instance is a user, and
   will return all the instances that match all the trackers the user is
   associated with.

All these manager methods  take keyword arguments to further filter the result
queryset and only fetch the actions you want (verbs, timestamp ...).


The ``trackers`` manager
------------------------

In addition to the ``actions`` attribute, ``actrack.connect`` makes another
helpful manager available: the ``trackers`` ::

    # this returns a Manager to fetch Tracker instances
    instance.trackers

``instance.tracker.tracking(\*\*kw)``
   All the trackers that are tracking the instance.

``instance.tracker.users(\*\*kw)``
   All the users who are tracking the instance (= the owners of the trackers
   tracking the instance returned by the above method).

``instance.tracker.owned(\*\*kw)``
   Works only if instance is a user, returns all the trackers owned by the
   instance.

``instance.tracker.tracked(\*models, \*\*kw)``
   Works only if instance is a user, returns all the objects (various types)
   tracked by the user. Be aware that if there are model class trackers, there
   can be model classes in the returned set.

``instance.tracker.all()``
   Overrides the normal ``all`` method. If instance is a user, will return a
   combination of ``instance.tracker.owned()`` and
   ``instance.tracker.tracking``. If not, it returns the same as
   ``instance.tracker.tracking``.

Similarly as above, these manager methods  take keyword arguments to further
filter the result queryset and only fetch the trackers you want (except
``tracker.tracked`` that returns instances of different models).


The default ``Action`` manager
------------------------------

Just a small word on the manager associated with the :ref:`Action` model: it
has a special method that returns all the actions followed by a given tracker:

``Action.objects.tracked_by(tracker, \*\*kw)``
   Fetches all the ``Action`` instances tracked by the tracker ``tracker``.


.. _Manager: https://docs.djangoproject.com/en/2.0/topics/db/managers/
