# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import gm2m.fields
import jsonfield.fields
import actrack.models
import django.utils.timezone
from actrack import settings
import actrack.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('actor_pk', models.CharField(max_length=255)),
                ('verb', models.CharField(max_length=255)),
                ('level', models.PositiveSmallIntegerField(default=30)),
                ('data', jsonfield.fields.JSONField(null=True, blank=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('actor_ct', models.ForeignKey(to='contenttypes.ContentType')),
                ('related', gm2m.fields.GM2MField(related_name='actions_as_related+', through_fields=(b'gm2m_src', b'gm2m_tgt', b'gm2m_ct', b'gm2m_pk'), pk_maxlength=16)),
                ('targets', gm2m.fields.GM2MField(related_name='actions_as_target+', through_fields=(b'gm2m_src', b'gm2m_tgt', b'gm2m_ct', b'gm2m_pk'), pk_maxlength=16)),
            ],
            options={
                'ordering': ('-timestamp',),
            },
        ),
        migrations.CreateModel(
            name='DeletedItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=255)),
                ('ctype', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Tracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tracked_pk', models.CharField(max_length=255, null=True)),
                ('verbs', actrack.fields.VerbsField(max_length=1000)),
                ('actor_only', models.BooleanField(default=True)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('fetched_elsewhere', models.ManyToManyField(related_name='_fetched_elsewhere_+', to='actrack.Action')),
                ('tracked_ct', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='trackers+', to=settings.USER_MODEL)),
            ],
            bases=(models.Model, actrack.models.TrackerBase),
        ),
        migrations.CreateModel(
            name='UnreadTracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('unread_actions', models.ManyToManyField(related_name='unread_in', to='actrack.Action')),
                ('user', actrack.fields.OneToOneField(related_name='unread_actions', to=settings.USER_MODEL)),
            ],
        ),
    ]
