# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-20 15:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aberowl', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_id', models.PositiveIntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('documentation', models.CharField(blank=True, max_length=255, null=True)),
                ('date_released', models.DateTimeField()),
                ('date_created', models.DateTimeField()),
                ('home_page', models.CharField(max_length=255)),
                ('has_ontology_language', models.CharField(max_length=127)),
                ('nb_classes', models.PositiveIntegerField(default=0)),
                ('nb_individuals', models.PositiveIntegerField(default=0)),
                ('nb_properties', models.PositiveIntegerField(default=0)),
                ('max_depth', models.PositiveIntegerField(default=0)),
                ('max_children', models.PositiveIntegerField(default=0)),
                ('avg_children', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='avg_children',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='description',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='home_page',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='max_children',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='max_depth',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='nb_classes',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='nb_individuals',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='nb_properties',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='url',
        ),
        migrations.AlterField(
            model_name='ontology',
            name='acronym',
            field=models.CharField(max_length=15, unique=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='ontology',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='aberowl.Ontology'),
        ),
    ]