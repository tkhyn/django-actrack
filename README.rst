django-actrack
==============

|copyright| 2014-2018 Thomas Khyn

``django-actrack`` is an activity tracker for the Django framework. It enables
recording any activity by any actor, relative to any number of targets or
related objects, with or without additional data. The activity can then be
retrieved through custom feeds.

It has been tested with Django 2.2.* and 3.0.* and their matching Python versions (3.5 to 3.8).

If you like django-actrack and find it useful, you may want to thank me and
encourage future development by sending a few mBTC / mBCH / mBSV at this address:
``1EwENyR8RV6tMc1hsLTkPURtn5wJgaBfG9``.

Features
--------

- Actions are defined by an actor, a verb and optional targets and related
  objects (yes, from any model and as many as you want, thanks to django-gm2m_)
  as well as additional data
- Convenient accessors to relevant actions from any model instance (such as
  ``userX.actions.feed()``)
- Users can track objects for specific action types (verbs)
- Deleted items do not disappear from the activity tracker
- Unread/read status actions
- Automatic grouping when identical or similar actions occur close to one
  another
- Full customisation support for actions combination (e.g. if action A implies
  action B, do not log action B)

Documentation
-------------

The documentation is hosted on readthedocs_. You'll find a quick start and
the description of all django-actrack's advanced features.


.. |copyright| unicode:: 0xA9

.. _django-gm2m: https://bitbucket.org/tkhyn/django-gm2m
.. _readthedocs: http://django-actrack.readthedocs.io/en/stable
