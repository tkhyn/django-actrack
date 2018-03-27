from collections import defaultdict
from inspect import isclass

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils import six

from gm2m.signals import deleting

from .compat import GenericForeignKey
from . import deletion


class ModelGFK(GenericForeignKey):
    """
    A generic foreign key that allows null primary key values to link the
    model class instead of an instance
    """

    def get_content_type(self, obj=None, id=None, using=None):
        if obj is not None:
            return get_content_type(obj)
        else:
            return super(ModelGFK, self).get_content_type(None, id, using)

    def instance_pre_init(self, signal, sender, args, kwargs, **_kwargs):
        """
        Override that allows value to be a class
        """
        if self.name in kwargs:
            value = kwargs.pop(self.name)
            if value is not None:
                kwargs[self.ct_field] = self.get_content_type(obj=value)
                kwargs[self.fk_field] = get_pk(value)
            else:
                kwargs[self.ct_field] = None
                kwargs[self.fk_field] = None

    def __get__(self, instance, cls=None):
        """
        Returns the model class instead of a model instance if the primary
        key is None
        Otherwise implementation is identical to GenericForeignKey.__get__
        """
        if instance is None:
            return self

        f = self.model._meta.get_field(self.ct_field)
        ct_id = getattr(instance, f.get_attname(), None)
        pk_val = getattr(instance, self.fk_field)

        rel_obj = self.get_cached_value(instance, default=None)
        if rel_obj is not None:
            ct = self.get_content_type(obj=rel_obj, using=instance._state.db)
            if ct_id != ct.id:
                rel_obj = None
            else:
                pk = rel_obj._meta.pk
                if pk is None:
                    # pk is None, we should return the model class
                    rel_obj = ct.model_class()
                else:
                    # If the primary key is a remote field, use the referenced
                    # field's to_python().
                    to_python_field = pk
                    # Out of an abundance of caution, avoid infinite loops.
                    seen = {to_python_field}
                    while to_python_field.remote_field:
                        to_python_field = to_python_field.target_field
                        if to_python_field in seen:
                            break
                        seen.add(to_python_field)
                    pk_to_python = to_python_field.to_python
                    if pk_to_python(pk_val) != rel_obj._get_pk_val():
                        rel_obj = None
                    else:
                        return rel_obj
        if ct_id is not None:
            ct = self.get_content_type(id=ct_id, using=instance._state.db)
            if pk_val is None:
                rel_obj = ct.model_class()
            else:
                try:
                    rel_obj = ct.get_object_for_this_type(pk=pk_val)
                except ObjectDoesNotExist:
                    pass
        self.set_cached_value(instance, rel_obj)
        return rel_obj

    def __set__(self, instance, value):
        """
        Override that allows value to be a class
        """
        ct = None
        fk = None
        if value is not None:
            ct = self.get_content_type(obj=value)
            fk = get_pk(value)

        setattr(instance, self.ct_field, ct)
        setattr(instance, self.fk_field, fk)
        self.set_cached_value(instance, value)


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

        base_mngr = self.remote_field.model._base_manager

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
            for attname in ('targets', 'related'):
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
                results = deleting.send(sender=self.remote_field.field,
                                        del_objs=objs, rel_objs=qs)
            else:
                results = []

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

    model_name = field.model._meta.model_name

    if not name:
        name = '%s_as_%s' % (model_name, field.name)

    if not related_name:
        related_name = '%s_%ss_in_%%(class)s' % (field.name,
                                                 tgt._meta.model_name)

    kwargs = {
        'content_type_field': '%s_ct' % field.name,
        'object_id_field': '%s_pk' % field.name,
        'related_query_name': related_name,
        'on_delete': on_delete,
    }
    ActrackGenericRelation(src, **kwargs) \
        .contribute_to_class(tgt, name)


def get_pk(obj):
    return None if isclass(obj) else obj.pk


def get_content_type(obj):
    ct_mngr = ContentType.objects
    try:
        # obj is a model instance, retrieve database
        qs = ct_mngr.db_manager(obj._state.db)
    except AttributeError:
        # obj is a model class
        qs = ct_mngr
    return qs.get_for_model(obj)
