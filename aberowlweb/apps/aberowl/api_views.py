from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import json
import itertools
from django.conf import settings
from collections import defaultdict
from gevent.pool import Pool
import time

from aberowl.models import Ontology

ELASTIC_SEARCH_URL = getattr(
    settings, 'ELASTIC_SEARCH_URL', 'http://localhost:9200/aberowl/')
ABEROWL_API_URL = getattr(
    settings, 'ABEROWL_API_URL', 'http://localhost:8080/api/')


def make_request(url):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            res = r.json()
            if 'result' in res:
                return res['result']
    except Exception as e:
        print(url, e)
    return []


def search(query_type, query_data):
    try:
        r = requests.post(
            ELASTIC_SEARCH_URL + query_type + '/_search',
            data=json.dumps(query_data),
            timeout=5)
        return r.json()
    except Exception as e:
        return {'hits': {'hits': []}}


class QueryOntologiesAPIView(APIView):

    def get(self, request, format=None):
        query = request.GET.get('query', None)

        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide query parameter!'})
        
        fields = ['name', 'lontology', 'description']
        query_list = []
        for field in fields:
            q = { 'match': { field: { 'query': query } } }
            query_list.append(q)
        omap = { 'query': { 'bool': { 'should': query_list } } }
        result = search('ontology', omap)
        data = []
        for hit in result['hits']['hits']:
            item = hit['_source']
            data.append(item)
        data = sorted(data, key=lambda x: len(x['name']))
        return Response(data)
        

class QueryNamesAPIView(APIView):

    def get(self, request, format=None):
        
        query = request.GET.get('query', None)
        ontology = request.GET.get('ontology', None)
        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide query parameter!'})
    
        fields = [
            ('label', 100),
            ('ontology', 1000),
            ('oboid', 10000),
            ('definition', 3),
            ('synonym', 75)]

        query_list = []

        for query_item in query.split():
            omap = {}
            omap['dis_max'] = {}
            omap['dis_max']['queries'] = []

            for field, boost in fields:
                q = {
                    'match': { field : { 'query': query_item, 'boost': boost } }
                }
                omap['dis_max']['queries'].append(q)
                query_list.append(omap)
        if ontology is not None:
            query_list.append({ 'match': { 'ontology': ontology } })

        f_query = {
            'query': { 'bool': { 'must': query_list } },
            'from': 0,
            'size': 1000}

        result = search("owlclass", f_query)

        data = defaultdict(list)
        for hit in result['hits']['hits']:
            item = hit['_source']
            data[item['label'][0]].append(item)
        ret = []
        for hit in result['hits']['hits']:
            label = hit['_source']['label'][0]
            if label in data:
                ret.append([label, data[label]])
                del data[label]
        return Response(ret)




class BackendAPIView(APIView):


    def __init__(self, *args, **kwargs):
        super(BackendAPIView, self).__init__(*args, **kwargs)
    

    def get(self, request, format=None):
        query_string = request.GET.urlencode()
        ontology = request.GET.get('ontology', None)
        script = request.GET.get('script', None)

        if script is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide script parameter!'})
        try: 
            if ontology is not None:
                queryset = Ontology.objects.filter(acronym=ontology)
                if queryset.exists():
                    ontology = queryset.get()
                    if ontology.nb_servers:
                        url = ontology.get_api_url() + script + '?' + query_string
                        r = requests.get(url)
                        return Response(r.json())
                    else:
                        raise Exception('API server is down!')
                else:
                    raise Exception('Ontology does not exist!')
            else:
                queryset = Ontology.objects.filter(nb_servers__gt=0)
                if queryset.exists():
                    url = ABEROWL_API_URL + script + '?' + query_string
                    r = requests.get(url)
                    return Response(r.json())
                else:
                    raise Exception('API server is down!')
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})
        
                

