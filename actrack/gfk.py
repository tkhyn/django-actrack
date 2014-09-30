from django.contrib.contenttypes.generic import GenericRelation

from .compat import related_attr_name, get_model_name


def add_relation(tgt, field, name=None, related_name=None):
    """
    Creates a generic reverse relation from a target model to the source model
    relative to the specified field
    """
    if not name:
        name = '%s_as_%s' % (get_model_name(field.model), field.name)

    if not related_name:
        related_name = '%s_with_%s_as_%s' % (
            get_model_name(field.model),
            get_model_name(tgt),
            field.name
        )

    kwargs = {
        'content_type_field': '%s_ct',
        'object_id_field': '%s_pk',
        related_attr_name: related_name
    }
    GenericRelation('actrack.Action', **kwargs) \
        .contribute_to_class(tgt, name)
