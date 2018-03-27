from .descriptors import ActrackDescriptor
from .settings import ACTIONS_ATTR, TRACKERS_ATTR


def connect(*args, **kwargs):
    """
    Model decorator to create relationships between the given model class
    and the Action and Tracker models

    @connect
    class MyModel

    @connect(use_del_items=False)
    class MyOtherModel

    or, alternatively, for existing models:

    connect(ExistingModel, **options)

    """

    # to avoid django complaining about apps not loaded yet
    from .gfk import add_relation
    from .models import Action, Tracker, GM2M_ATTRS
    from .managers.inst import InstActionManager, InstTrackerManager
    from .deletion import CASCADE, DO_NOTHING_SIGNAL

    def mk_decorator(use_del_items=True):

        on_delete_src = CASCADE

        if use_del_items:
            on_delete_tgt = DO_NOTHING_SIGNAL
        else:
            on_delete_tgt = CASCADE

        def actual_connect(cls):
            """
            The actual decorator for the class
            """

            # adding generic relations
            for field, model in (('actor', Action), ('tracked', Tracker)):
                model_name = model._meta.model_name
                rel_name = '%ss_as_%s' % (model_name, field)
                add_relation('actrack.%s' % model_name, cls,
                    field=getattr(model, field), name=rel_name,
                    related_name='%s_%ss_in_%%(class)s'
                                 % (field, cls._meta.model_name),
                    on_delete=on_delete_tgt
                )
                # we want a hidden relation, so the attribute should not be set
                delattr(cls, rel_name)

            # adding hidden gm2m relations and modifying on_delete handlers
            for attr in GM2M_ATTRS:
                descriptor = getattr(Action, attr)
                descriptor.add_relation(cls, on_delete=on_delete_tgt)
                descriptor.field.remote_field.on_delete_src = on_delete_src

            # adding actions and trackers managers
            for name, mngr in ((ACTIONS_ATTR, InstActionManager),
                               (TRACKERS_ATTR, InstTrackerManager)):
                ActrackDescriptor(mngr).add_to_model(cls, name)

            return cls

        return actual_connect

    if args:
        # the decorator is used 'as is' without in-line arguments
        # we use the decorator generator (with possible provided kwargs)
        # and call it with the 1st argument, which is the decorated class
        return mk_decorator(**kwargs)(args[0])
    else:
        # kwargs are provided to the decorator
        # e.g @track(use_del_items=True)
        return mk_decorator(**kwargs)
