"""
Defines an improved OneToOneField and a VerbsField
"""

from django.db import models

from .descriptors import ReverseOneToOneDescriptor


class OneToOneField(models.OneToOneField):
    """
    A OneToOneField that creates the related object if it does not exist
    Taken from django-annoying
    """
    related_accessor_class = ReverseOneToOneDescriptor


class VerbsField(models.TextField):
    """
    Defines a field to store a set of verbs. It is preferable to use a set of
    verbs than a M2M field in Follow for performance reasons
    """

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ';')
        kwargs['null'] = True
        super(VerbsField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(VerbsField, self).deconstruct()
        del kwargs['null']
        if self.token != ';':
            kwargs['token'] = self.token
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return set()
        return set(value.split(self.token))

    def to_python(self, value):
        if not value:
            return set()
        if isinstance(value, str):
            return set(value.split(self.token))
        return set(value)

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if not value:
            return
        assert(isinstance(value, (list, tuple, set)))
        return self.token.join({str(s) for s in value})

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)
