Quick start
===========


Installation
------------

As straightforward as it can be, using pip::

   pip install django-actrack

You then need to modify your ``INSTALLED_APPS`` settings:

- make sure it contains ``django.contrib.contenttypes``
- add ``'actrack'`` and ``gm2m``


First steps
-----------

All right, let's start tracking.

Logging activity
................

To track actions, the first things we need are ... actions. Let's generate and
log some. We use the ``actrack.log`` function::

   import actrack

   actrack.log(user, 'had_lunch')

``user`` can be a user model instance (for example an instance of
``django.contrib.auth``'s ``User`` model) but it could as well be any instance
of any model. It could be a train, for example (though trains usually don't
have lunch).

You can also provide targets and related objects to add information to the
action::

   actrack.log(train, 'left_station', targets=[origin], related=[destination])

Or any relevant data as key-word arguments::

   actrack.log(train, 'arrived', time=now())

OK, we've generated a few actions, let's see how we can retrieve them.

Tracking activity
.................

``django-actrack`` uses trackers to retrieve actions associated to instances.
If you want the user ``user`` (here it needs to be an actual user, see below) to
track all actions related to a given ``train``, you can create a tracker using
``actrack.track``::

   actrack.track(user, train)

This creates a tracker entry in the database that will be used to retrieve
every activity related to ``train``. ``train`` could have been any other
instance of any other model, or even a model class itself to follow any instance
of that model, but ``user`` must be an instance of the ``USER_MODEL`` specified
in the :ref:`settings` (which defaults to ``AUTH_USER_MODEL_``).

Retrieving activity
...................

To retrieve every action matching this tracker, ``django-actrack`` can provide
convenient accessors, provided you have connected the model to it beforehand
using the ``@actrack.connect`` decorator::

   @actrack.connect
   class Train(models.Models):
      ...

'Connecting' ``django-actrack`` with a model will expose an ``actions``
attribute on every instance of the model::

   # all the actions where the train is involved
   all_train_actions = train.actions.all()

   # actions where the train is involved as an actor, target or related object
   train_actions_as_actor = train.actions.as_actor()
   train_actions_as_target = train.actions.as_target()
   train_actions_as_related = train.actions.as_related()

All the above will work for a given user instance or any instance which model
has been connected to ``django-actrack`` via the ``connect`` decorator.

Additionally, for user instances, we can invoke::

   user_feed = user.actions.feed()

And this will fetch all the actions related to all the objects the user is
tracking (trains, airplanes, cars, anything ...)


.. note::
   It is not always possible to use the ``connect`` decorator this way.
   The most common example is ``django.contrib.auth.User``. We therefore use
   ``connect`` as a simple function, somewhere in our app (for example in an
   ``AppConfig`` subclass' ``ready()`` method) so that it is executed when
   Django starts::

      actrack.connect(UserModel)

Next steps
..........

Want to track more trains? Head to the :ref:`features` page to discover all the
advanced stuff ``django-actrack`` can offer,


.. _AUTH_USER_MODEL: https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-AUTH_USER_MODEL
