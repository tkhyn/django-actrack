import warnings

from django.utils import six

# exposes CASCADE, CASCADE_SIGNAL, etc ...
from gm2m.deletion import *


class DelItemDescriptionWarning(RuntimeWarning):
    pass


def get_del_item(instance):

    from django.contrib.contenttypes.models import ContentType
    from .models import DeletedItem

    try:
        # retrieve the existing deleted item
        del_item = DeletedItem.registry[instance]
    except KeyError:
        # extract instance description to generate new deleted item

        opts = instance._meta

        try:
            description = instance.deleted_item_description()
        except AttributeError:
            description = six.text_type(instance)
            warnings.warn(
                'Description for an instance of model "%s.%s" was '
                'generated from implicit conversion to string. You may '
                'want to add a "deleted_item_description" method to the '
                'model.' % (opts.app_label, opts.object_name),
                DelItemDescriptionWarning)

        try:
            serialization = instance.deleted_item_serialization()
        except AttributeError:
            serialization = {'pk': instance.pk}
            warnings.warn(
                'Serialization for an instance of model "%s.%s" was '
                'generated automatically from the primary key. You may '
                'want to add a "deleted_item_serialization" method to the '
                'model.' % (opts.app_label, opts.object_name),
                DelItemDescriptionWarning)

        del_item = DeletedItem.objects.create(
            ctype=ContentType.objects.get_for_model(instance.__class__),
            description=description, serialization=serialization
        )

        DeletedItem.registry.add(instance, del_item)

    return del_item


def handle_deleted_items(sender, **kwargs):
    """
    Creates the matching DeletedItem instances corresponding to the list of
    objects provided under the ``objs`` keyword argument
    """

    from django.contrib.contenttypes.models import ContentType
    from .models import DeletedItem

    # the objects being deleted
    instances = kwargs.pop('del_objs')

    # the qs of concerned through instances
    through_instances = kwargs.pop('rel_objs')

    delitem_ct = ContentType.objects.get_for_model(DeletedItem)

    # create one deleted item per object
    for inst in instances:

        # don't do anything if inst is already a DeletedItem or if it has
        # already been processed
        if isinstance(inst, DeletedItem):
            continue

        # extract content type and primary key data
        inst_ct = ContentType.objects.get_for_model(inst.__class__)
        inst_id = inst.pk

        del_item = get_del_item(inst)

        # update in database
        if hasattr(sender, 'content_type_field_name'):
            # GFK update (Action's actor or Tracker's tracked)
            ct_field_name = sender.content_type_field_name
            pk_field_name = sender.object_id_field_name
            through_instances.filter(**{
                ct_field_name: inst_ct, pk_field_name: inst_id
            }).update(**{
                ct_field_name: delitem_ct, pk_field_name: del_item.pk
            })
        else:
            # targets or related field update via through model manager
            through_instances.filter(gm2m_ct=inst_ct, gm2m_pk=inst_id) \
                .update(gm2m_ct=delitem_ct, gm2m_pk=del_item.pk)
