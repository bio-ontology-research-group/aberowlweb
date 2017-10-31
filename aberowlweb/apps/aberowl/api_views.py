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

event_pool = Pool(1000)


def make_request(url):
    r = requests.get(url)
    if r.status_code == 200:
        res = r.json()
        if 'result' in res:
            return res['result']
    return []


def search(query_type, query_data):
    r = requests.post(
        ELASTIC_SEARCH_URL + query_type + '/_search',
        data=json.dumps(query_data))
    return r.json()


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
            ('synonym', 75),
            ('AberOWL-catch-all', 0.01),
            ('AberOWL-subclass', 25),
            ('AberOWL-equivalent', 25),]

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
            data[item['first_label']].append(item)
        
        return Response(data)




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
    
        if ontology is not None:
            queryset = Ontology.objects.filter(acronym=ontology)
            if queryset.exists():
                ontology = queryset.get()
                if ontology.is_running:
                    url = ontology.get_api_url() + script + '?' + query_string
                    r = requests.get(url)
                    return Response(r.json())
                else:
                    return Response({
                        'status': 'error', 'message': 'API server is down!'})
            else:
                return Response(
                    {'status': 'error', 'message': 'Ontology does not exist!'})
        else:
            queryset = Ontology.objects.filter(is_running=True)
            urls = []
            
            for ontology in queryset:
                url = ontology.get_api_url() + script + '?' + query_string
                urls.append(url)
            start_time = time.time()
            results = event_pool.map(make_request, urls)
            result = list(itertools.chain.from_iterable(results))
            print('Finished in', time.time() - start_time)
            return Response({'result': result})

