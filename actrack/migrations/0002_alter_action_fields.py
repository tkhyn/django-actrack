# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('actrack', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='actor_ct',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True),
        ),
        migrations.AlterField(
            model_name='action',
            name='actor_pk',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='action',
            name='data',
            field=jsonfield.fields.JSONField(default={}),
        ),
    ]
