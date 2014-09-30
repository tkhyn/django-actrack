import django
from django.db.models.options import Options


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
