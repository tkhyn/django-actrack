# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actrack', '0002_adds_pk_maxlength'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='level',
            field=models.PositiveSmallIntegerField(default=30),
        ),
    ]
