"""
Defines a field to store a set of verbs. It is preferable to use a set of
verbs than a M2M field in Follow for performance reasons
"""

from django.db import models
from django.utils import six


class VerbsField(six.with_metaclass(models.SubfieldBase, models.TextField)):

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ';')
        kwargs['null'] = True
        super(VerbsField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return set()
        if isinstance(value, six.string_types):
            return set(value.split(self.token))
        return set(value)

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if not value:
            return
        assert(isinstance(value, (list, tuple, set)))
        return self.token.join([str(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


try:
    from south.modelsinspector import add_introspection_rules
except:
    pass
else:
    add_introspection_rules([
        (
            [VerbsField],  # Class(es) these apply to
            [],  # Positional arguments (not used)
            {  # Keyword argument
                "token": ["token", {"default": ","}],
            },
        ),
    ], ["^actstream\.fields\.VerbsField"])
