# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField


class Ontology(models.Model):
    CLASSIFIED = 'Classified'
    UNLOADABLE = 'Unloadable'
    INCOHERENT = 'Incoherent'
    UNKNOWN = 'Unknown'
    STATUS_CHOICES = (
        (CLASSIFIED, CLASSIFIED),
        (UNLOADABLE, UNLOADABLE),
        (INCOHERENT, INCOHERENT),
        (UNKNOWN, UNKNOWN),
    )
    acronym = models.CharField(max_length=15)
    name = models.CharField(max_length=127)
    description = models.TextField()
    url = models.CharField(max_length=255)
    home_page = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_ontologies')
    date_created = models.DateTimeField()
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='modified_ontologies')
    date_modified = models.DateTimeField(blank=True, null=True)
    
    date_updated = models.DateTimeField(blank=True, null=True)
    topics = ArrayField(
        models.CharField(max_length=127), blank=True, null=True)
    species = ArrayField(
        models.CharField(max_length=127), blank=True, null=True)
    status = models.CharField(
        max_length=31, choices=STATUS_CHOICES, default=UNKNOWN)
    nb_classes = models.PositiveIntegerField(default=0)
    nb_individuals = models.PositiveIntegerField(default=0)
    nb_properties = models.PositiveIntegerField(default=0)
    max_depth = models.PositiveIntegerField(default=0)
    max_children = models.PositiveIntegerField(default=0)
    avg_children = models.PositiveIntegerField(default=0)
    
    
