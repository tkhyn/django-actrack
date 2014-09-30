import django
from django.db.models.options import Options


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
