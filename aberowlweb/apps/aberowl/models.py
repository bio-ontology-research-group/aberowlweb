# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils import timezone
from django.conf import settings
import os

ABEROWL_API_URL = getattr(
    settings, 'ABEROWL_API_URL', 'http://localhost:8080/api/')

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
    BIOPORTAL = 'bioportal'
    OBOFOUNDRY = 'obofoundry'
    MANUAL = 'manual'
    
    acronym = models.CharField(max_length=63, unique=True)
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_ontologies')
    source = models.CharField(max_length=15, default=MANUAL)
    date_created = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='modified_ontologies')
    date_modified = models.DateTimeField(blank=True, null=True)
    
    date_updated = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=31, choices=STATUS_CHOICES, default=UNKNOWN)
    topics = ArrayField(
        models.CharField(max_length=127), blank=True, null=True)
    species = ArrayField(
        models.CharField(max_length=127), blank=True, null=True)
    nb_servers = models.PositiveIntegerField(default=0)
    
    is_obsolete = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Ontologies'

    def __str__(self):
        return self.acronym + ' - ' + self.name

    def get_latest_submission(self):
        submission = self.submissions.order_by('-pk').first()
        return submission

    def get_api_url(self):
        return ABEROWL_API_URL

    
class Submission(models.Model):
    LANGUAGE_CHOICES = (
        ('OWL', 'OWL'),
        ('OBO', 'OBO'),
        ('SKOS', 'SKOS'),
        ('UMLS', 'UMLS')
    )
    ontology = models.ForeignKey(
        Ontology, on_delete=models.CASCADE, related_name='submissions')
    submission_id = models.PositiveIntegerField()
    domain = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    documentation = models.CharField(max_length=255, blank=True, null=True)
    publication = models.CharField(max_length=255, blank=True, null=True)
    publications = JSONField(blank=True, null=True)
    products = JSONField(blank=True, null=True)
    taxon = JSONField(blank=True, null=True)
    date_released = models.DateTimeField()
    date_created = models.DateTimeField()
    home_page = models.CharField(max_length=255, blank=True, null=True)
    version = models.TextField(blank=True, null=True)
    has_ontology_language = models.CharField(
        max_length=15, verbose_name='Ontology Language',
        choices=LANGUAGE_CHOICES)
    nb_classes = models.PositiveIntegerField(default=0, blank=True, null=True)
    nb_individuals = models.PositiveIntegerField(
        default=0, blank=True, null=True)
    nb_properties = models.PositiveIntegerField(
        default=0, blank=True, null=True)
    max_depth = models.PositiveIntegerField(default=0, blank=True, null=True)
    max_children = models.PositiveIntegerField(default=0, blank=True, null=True)
    avg_children = models.PositiveIntegerField(default=0, blank=True, null=True)
    classifiable = models.BooleanField(default=False)
    nb_inconsistent = models.PositiveIntegerField(default=0)
    indexed = models.BooleanField(default=False)

    md5sum = models.CharField(
        max_length=32, blank=True, null=True)

    class Meta:
        unique_together = (
            ('ontology', 'submission_id'),
            ('ontology', 'md5sum'),)

    def __str__(self):
        return str(self.ontology) + ' - ' + str(self.submission_id)

    def get_filepath(self, folder=None):
        if folder is None:
            folder = str(self.submission_id)
        filename = (self.ontology.acronym  + '.'
                    + self.has_ontology_language).lower()
        filedir = (settings.MEDIA_ROOT + 'ontologies/' + self.ontology.acronym
                + '/' + folder + '/')
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        return filedir + filename

