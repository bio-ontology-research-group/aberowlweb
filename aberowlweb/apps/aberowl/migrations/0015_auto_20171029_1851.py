# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-29 18:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aberowl', '0014_auto_20171029_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ontology',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='submission',
            name='documentation',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='home_page',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='publication',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]