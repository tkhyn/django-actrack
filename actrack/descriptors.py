"""
Descriptors to be used as attributes for models.
"""

try:
    # django 1.11
    from django.db.models.fields.related_descriptors \
        import ReverseOneToOneDescriptor as OriginalReverseOneToOneDescriptor
except ImportError:
    from django.db.models.fields.related \
        import SingleRelatedObjectDescriptor as OriginalReverseOneToOneDescriptor

from django.db.transaction import atomic


class ReverseOneToOneDescriptor(OriginalReverseOneToOneDescriptor):
    """
    For OneToOneField, inspiration from django-annoying
    """
    @atomic
    def __get__(self, instance, instance_type=None):
        try:
            model = self.related.related_model
        except AttributeError:
            model = self.related.model

        try:
            return super(ReverseOneToOneDescriptor, self) \
                .__get__(instance, instance_type)
        except model.DoesNotExist:
            # actually a RelatedObjectDoesNotExist exception
            # this creates the object if it does not exist
            # we use get_or_create to better handle race conditions than save()
            model.objects.get_or_create(**{self.related.field.name: instance})
            try:
                delattr(instance, self.cache_name)
            except AttributeError:
                pass
            return super(ReverseOneToOneDescriptor, self) \
                .__get__(instance, instance_type)


class ActrackDescriptor(object):
    """
    Return the actions or trackers which refer to a model instance
    """

    def __init__(self, manager_cls):
        self.manager_cls = manager_cls

    def add_to_model(self, model, attr_name):
        setattr(model, attr_name, self)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return self.manager_cls(instance)

    def __set__(self):
        raise SyntaxError('Attempting to set a read-only value')
