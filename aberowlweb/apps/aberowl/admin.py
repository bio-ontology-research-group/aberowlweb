# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from aberowl.models import Ontology, Submission

# Register your models here.
admin.site.register(Ontology)
admin.site.register(Submission)
