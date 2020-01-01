# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import TemplateView, DetailView, ListView
import requests
from django.conf import settings
from django.http import Http404
import redis
from aberowl import redis_pool
import json

from aberowl.models import Ontology, Submission
from aberowl.serializers import OntologySerializer, SubmissionSerializer
from aberowlweb.apps.aberowl.ont_server_request_processor import OntServerRequestProcessor
from rest_framework.renderers import JSONRenderer


ABEROWL_API_URL = getattr(
    settings, 'ABEROWL_API_URL', 'http://localhost/')


ont_server = OntServerRequestProcessor()

class MainView(TemplateView):

    template_name = 'aberowl/main.html'

    def get_context_data(self, *args, **kwargs):
        context = super(TemplateView, self).get_context_data(*args, **kwargs)
        return context


class OntologyListView(ListView):

    template_name = 'aberowl/list_ontologies.html'
    model = Ontology

    def get_context_data(self, *args, **kwargs):
        context = super(ListView, self).get_context_data(*args, **kwargs)
        ontologies = self.get_queryset().filter(
            status=Ontology.CLASSIFIED, nb_servers__gt=0)
        data = OntologySerializer(ontologies, many=True).data
        context['ontologies'] = JSONRenderer().render(data)
        return context


class OntologyDetailView(DetailView):

    template_name = 'aberowl/view_ontology.html'
    model = Ontology
    slug_field = 'acronym'
    slug_url_kwarg = 'onto'

    def get_context_data(self, *args, **kwargs):
        context = super(DetailView, self).get_context_data(*args, **kwargs)
        ontology = self.get_object()
        submission = ontology.get_latest_submission()
        if submission is None:
            raise Http404
        
        data = OntologySerializer(ontology).data
        data['classes'] = []
        data['properties'] = []
        try:
            rq = requests.get(
                ontology.get_api_url()
                + 'runQuery.groovy?type=subclass&direct=true&query=<http://www.w3.org/2002/07/owl%23Thing>&ontology='
                + ontology.acronym)
            res = rq.json()
            if 'result' in res:
                data['classes'] = res['result']
            else:
                print(res)
            res = ont_server.find_ontology_object_properties(ontology.acronym)
            if 'result' in res:
                data['properties'] = res['result']
            else:
                print(res)
        except Exception as e:
            print(e)
        
        downloads = []
        for sub in ontology.submissions.all().order_by('-date_released'):
            downloads.append([
                sub.version,
                sub.date_released.strftime('%Y-%m-%d'),
                sub.get_filepath()])
        data['downloads'] = downloads
        context['ontology'] = json.dumps(data)
        return context
