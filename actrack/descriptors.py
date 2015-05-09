"""
Descriptors to be used as attributes for models.
"""

from django.db.models.fields import related


class SingleRelatedObjectDescriptor(related.SingleRelatedObjectDescriptor):
    """
    For OneToOneField, taken from django-annoying
    """
    def __get__(self, instance, instance_type=None):
        try:
            model = self.related.related_model
        except:
            model = self.related.model

        try:
            return super(SingleRelatedObjectDescriptor, self) \
                .__get__(instance, instance_type)
        except model.DoesNotExist:
            # actually a RelatedObjectDoesNotExist exception
            # this creates the object if it does not exist
            obj = model(**{self.related.field.name: instance})
            obj.save()
            return super(SingleRelatedObjectDescriptor, self) \
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
