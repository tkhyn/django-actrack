from collections import defaultdict

from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils import six

from gm2m.signals import deleting

from . import deletion
from .compat import related_attr_name, get_model_name


class ActrackGenericRelation(GenericRelation):

    def __init__(self, to, **kwargs):
        # we need to remove on_delete from the kwargs and set self.on_delete
        # afterwards. If not it is overriden by the supers' __init__ methods
        on_delete = kwargs.pop('on_delete')
        super(ActrackGenericRelation, self).__init__(to, **kwargs)
        self.on_delete = on_delete

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        """
        Return all objects related to objs
        The returned result will be passed to Collector.collect, so one should
        not use the deletion functions as such
        """

        base_mngr = self.rel.to._base_manager

        if self.on_delete is not deletion.DO_NOTHING:
            # collect related objects

            # first sort them by content type, as nothing guarantees that objs
            # is an homogeneous collection
            objs_by_ct = defaultdict(lambda: [])
            for obj in objs:
                objs_by_ct[get_content_type(obj).pk].append(obj.pk)

            q = Q()
            ct_field_name = '%s__pk' % self.content_type_field_name
            pk_field_name_in = "%s__in" % self.object_id_field_name
            for ct, pks in six.iteritems(objs_by_ct):
                q = q | Q(**{
                    ct_field_name: ct,
                    pk_field_name_in: pks
                })

            # GM2M relations for action model
            for attname in ('changed', 'related'):
                if hasattr(base_mngr.model, attname):
                    for ct, pks in six.iteritems(objs_by_ct):
                        q = q | Q(**{
                            'action_%s__gm2m_ct__pk' % attname: ct,
                            'action_%s__gm2m_pk__in' % attname: pks
                        })

            # generate queryset
            qs = base_mngr.filter(q)

            # get signal receiver's results
            if self.on_delete in deletion.handlers_with_signal:
                results = deleting.send(sender=self.rel.field,
                                        del_objs=objs, rel_objs=qs)

            if self.on_delete in (deletion.CASCADE, deletion.CASCADE_SIGNAL) \
            or self.on_delete is deletion.CASCADE_SIGNAL_VETO \
            and not any(r[1] for r in results):
                # if CASCADE must be called or if no receiver returned a veto
                # we return the qs for deletion
                # note that it is an homogeneous queryset (as Collector.collect
                # which is called afterwards only works with homogeneous
                # collections)
                return qs

        # do not delete anything by default
        empty_qs = base_mngr.none()
        empty_qs.query.set_empty()
        return empty_qs


def add_relation(src, tgt, field, name=None, related_name=None,
                 on_delete=deletion.CASCADE):
    """
    Creates a reverse relation from a target model to the source model
    relative to the specified GenericForeignKey field
    """

    if not name:
        name = '%s_as_%s' % (get_model_name(field.model), field.name)

    if not related_name:
        related_name = '%s_with_%(class)s_as_%s' % (
            get_model_name(field.model),
            field.name
        )

    kwargs = {
        'content_type_field': '%s_ct' % field.name,
        'object_id_field': '%s_pk' % field.name,
        related_attr_name: related_name,
        'on_delete': on_delete,
    }
    ActrackGenericRelation(src, **kwargs) \
        .contribute_to_class(tgt, name)


def get_content_type(obj):
    ct_mngr = ContentType.objects
    try:
        # obj is a model instance, retrieve database
        qs = ct_mngr.db_manager(obj._state.db)
    except AttributeError:
        # obj is a model class
        qs = ct_mngr
    return qs.get_for_model(obj)
