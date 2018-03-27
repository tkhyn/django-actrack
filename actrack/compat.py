import django
from django.contrib.contenttypes.fields import GenericForeignKey


if django.VERSION < (2,0):
    _GenericForeignKey = GenericForeignKey


    class GenericForeignKey(_GenericForeignKey):
        """
        Implement methods available in Django 2.0
        """

        def get_cached_value(self, instance, default=None):
            getattr(instance, self.cache_attr, default)

        def set_cached_value(self, instance, value):
            setattr(instance, self.cache_attr, value)
