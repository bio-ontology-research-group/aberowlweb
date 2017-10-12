# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-11 08:40
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ontology',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acronym', models.CharField(max_length=15)),
                ('name', models.CharField(max_length=127)),
                ('description', models.TextField()),
                ('url', models.CharField(max_length=255)),
                ('home_page', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField()),
                ('date_modified', models.DateTimeField(blank=True, null=True)),
                ('date_updated', models.DateTimeField(blank=True, null=True)),
                ('topics', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=127), blank=True, null=True, size=None)),
                ('species', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=127), blank=True, null=True, size=None)),
                ('status', models.CharField(choices=[('Classified', 'Classified'), ('Unloadable', 'Unloadable'), ('Incoherent', 'Incoherent'), ('Unknown', 'Unknown')], default='Unknown', max_length=31)),
                ('nb_classes', models.PositiveIntegerField(default=0)),
                ('nb_individuals', models.PositiveIntegerField(default=0)),
                ('nb_properties', models.PositiveIntegerField(default=0)),
                ('max_depth', models.PositiveIntegerField(default=0)),
                ('max_children', models.PositiveIntegerField(default=0)),
                ('avg_children', models.PositiveIntegerField(default=0)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_ontologies', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_ontologies', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
