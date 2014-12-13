# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import gm2m.fields

from actrack import settings


class Migration(migrations.Migration):

    dependencies = [
        ('actrack', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='related',
            field=gm2m.fields.GM2MField(related_name='actions_as_related+', pk_maxlength=settings.PK_MAXLENGTH),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='targets',
            field=gm2m.fields.GM2MField(related_name='actions_as_target+', pk_maxlength=settings.PK_MAXLENGTH),
            preserve_default=True,
        ),
    ]
