# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import TemplateView
import requests
from django.conf import settings
import redis
from aberowl import redis_pool
import json


ABEROWL_API_SERVER = getattr(
    settings, 'ABEROWL_API_SERVER', 'http://localhost/')


class OntologiesListView(TemplateView):

    template_name = 'aberowl/list_ontologies.html'

    def get_context_data(self, *args, **kwargs):
        context = super(TemplateView, self).get_context_data(*args, **kwargs)

        rq = requests.get(ABEROWL_API_SERVER + 'service/api/listOntologies.groovy')
        onto_list = rq.json()
        rd = redis.Redis(connection_pool=redis_pool)
        ontologies = []
        for onto in onto_list:
            data = rd.get('ontos:' + onto)
            if data:
                ontologies.append(data)
        ontologies = '[' + ', '.join(ontologies) + ']'
        context['ontologies'] = ontologies
        return context
