# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-31 13:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aberowl', '0015_auto_20171029_1851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ontology',
            name='acronym',
            field=models.CharField(max_length=63, unique=True),
        ),
    ]
