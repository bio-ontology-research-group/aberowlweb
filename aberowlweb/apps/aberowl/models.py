# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings
import os


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
    acronym = models.CharField(max_length=31, unique=True)
    name = models.CharField(max_length=127)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_ontologies')
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
    server_ip = models.GenericIPAddressField(
        protocol='IPv4', default="127.0.0.1")
    port = models.PositiveIntegerField(unique=True)
    is_running = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Ontologies'

    def __str__(self):
        return self.acronym + ' - ' + self.name

    def get_latest_submission(self):
        submission = self.submissions.order_by('-pk').first()
        return submission

    def get_api_url(self):
        return 'http://' + self.server_ip + ':' + str(self.port) + '/api/'

    
class Submission(models.Model):
    ontology = models.ForeignKey(
        Ontology, on_delete=models.CASCADE, related_name='submissions')
    submission_id = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    documentation = models.CharField(max_length=127, blank=True, null=True)
    publication = models.CharField(max_length=127, blank=True, null=True)
    date_released = models.DateTimeField()
    date_created = models.DateTimeField()
    home_page = models.CharField(max_length=127, blank=True, null=True)
    version = models.CharField(max_length=127, blank=True, null=True)
    has_ontology_language = models.CharField(max_length=15)
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

    class Meta:
        unique_together = (('ontology', 'submission_id'),)

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

