# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-28 20:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aberowl', '0012_auto_20171028_2031'),
    ]

    operations = [
        migrations.AddField(
            model_name='ontology',
            name='server_ip',
            field=models.GenericIPAddressField(default='127.0.0.1', protocol='IPv4'),
        ),
    ]