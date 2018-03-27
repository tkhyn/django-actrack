Quick start
===========


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

``user`` could as well be any instance of any model, it does not have to be a
user. Could be a train, for example (though trains usually don't have lunch).

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
to ``AUTH_USER_MODEL``).

To retrieve every action matching this tracker, ``django-actrack`` provides
convenient accessors, provided you have connected the model to it beforehand::

   @actrack.connect
   class MyModel(models.Models):
      ...

However, it is not always possible to use this decorator in this manner. The
most common example is ``auth.User``. We therefore use ``connect`` as a simple
function, somewhere in our app (for example in an ``AppConfig`` subclass'
``ready()`` method) so that it is executed when it is loaded::

   actrack.connect(UserModel)

This will expose two attributes ``actions`` and ``trackers`` for every instance
of the model. We'll be able to do::

   for action in user.actions.feed():
      # iterate over all the actions user is tracking
