"""
Descriptors to be used as attributes for models. They return the actions or
trackers which refer to a model instance
"""


class ActrackDescriptor(object):

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
