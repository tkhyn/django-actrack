import inspect

import django
from django.db import models
from django.db.models.options import Options
from django.utils import six

try:
    from django.utils.timezone import now
except ImportError:
    from datetime.datetime import now

try:
    from django.apps import AppConfig
except ImportError:  # Django < 1.7
    AppConfig = object


try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
    get_user_model = lambda: User


related_attr_name = 'related_name'
if django.VERSION >= (1, 7):
    related_attr_name = 'related_query_name'


def get_model_name(x):
    """
    Retrieves the name of a model
    """
    opts = x if isinstance(x, Options) else x._meta
    try:
        return opts.model_name
    except AttributeError:
        # Django < 1.6
        return opts.object_name.lower()


def load_app():
    """
    Loads the application from models module for Django < 1.7
    """
    if django.VERSION < (1, 7):
        from .apps import ActrackConfig
        ActrackConfig().ready()


if django.VERSION < (1, 6):

    # We need to make sure that queryset related methods are available
    # under the old and new denomination (it is taken care of by
    # django.utils.deprecation.RenameMethodBase in Django >= 1.6)
    # A Metaclass is needed for that purpose

    class GetQSetRenamer(type):
        # inspired from django 1.6's RenameMethodsBase

        renamed_methods = (
            ('get_query_set', 'get_queryset'),
            ('get_prefetch_query_set', 'get_prefetch_queryset')
        )

        def __new__(cls, name, bases, attrs):
            new_class = super(GetQSetRenamer, cls).__new__(cls, name,
                                                           bases, attrs)

            for base in inspect.getmro(new_class):
                for renamed_method in cls.renamed_methods:
                    old_method_name = renamed_method[0]
                    old_method = base.__dict__.get(old_method_name)
                    new_method_name = renamed_method[1]
                    new_method = base.__dict__.get(new_method_name)

                    if not new_method and old_method:
                        # Define the new method if missing
                        setattr(base, new_method_name, old_method)
                    elif not old_method and new_method:
                        # Define the old method if missing
                        setattr(base, old_method_name, new_method)

            return new_class

    class Manager(six.with_metaclass(GetQSetRenamer, models.Manager)):
        pass
else:
    Manager = models.Manager
