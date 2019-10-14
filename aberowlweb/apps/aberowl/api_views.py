from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
import requests
import json
import itertools
from django.http import HttpResponse
from django.conf import settings
from collections import defaultdict
from gevent.pool import Pool
import time

from aberowl.models import Ontology
from aberowl.serializers import OntologySerializer
from elasticsearch import Elasticsearch


ELASTIC_SEARCH_URL = getattr(
    settings, 'ELASTIC_SEARCH_URL', 'http://localhost:9200/')
ELASTIC_SEARCH_USERNAME = getattr(
    settings, 'ELASTIC_SEARCH_USERNAME', '')
ELASTIC_SEARCH_PASSWORD = getattr(
    settings, 'ELASTIC_SEARCH_PASSWORD', '')
ELASTIC_ONTOLOGY_INDEX_NAME = getattr(
    settings, 'ELASTIC_ONTOLOGY_INDEX_NAME', 'aberowl_ontology')
ELASTIC_CLASS_INDEX_NAME = getattr(
    settings, 'ELASTIC_CLASS_INDEX_NAME', 'aberowl_owlclass')

ABEROWL_API_URL = getattr(
    settings, 'ABEROWL_API_URL', 'http://localhost:8080/api/')

es = None
esUrl = ELASTIC_SEARCH_URL.split(",")
if ELASTIC_SEARCH_USERNAME and ELASTIC_SEARCH_PASSWORD:
    es = Elasticsearch(esUrl, http_auth=(ELASTIC_SEARCH_USERNAME, ELASTIC_SEARCH_PASSWORD))
else :
    es = Elasticsearch(esUrl)

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


def search(indexName, query_data):
    try:
        res = es.search(index=indexName, body=query_data, request_timeout=15)
        return res
    except Exception as e:
        print("elasticsearch err", e)
        return {'hits': {'hits': []}}



class SearchClassesAPIView(APIView):

    def get(self, request, format=None):
        query = request.GET.get('query', None)
        ontology = request.GET.get('ontology', None)
        return self.process_query(query, ontology)

    def process_query(self, query, ontology):
        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide query parameter!'})
        if ontology is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide ontology parameter!'})
        try:
            query_list = [
                { 'match': { 'ontology': ontology } },
                { 'match_bool_prefix': { 'label': query.lower() } }
            ]
            docs = {
                'query': { 'bool': { 'must': query_list } },
                '_source': {'excludes': ['embedding_vector',]}
            }
            result = search(ELASTIC_CLASS_INDEX_NAME, docs)
            data = []
            for hit in result['hits']['hits']:
                item = hit['_source']
                data.append(item)
            data = sorted(data, key=lambda x: len(x['label']))
            result = {'status': 'ok', 'result': data}
            return Response(result)
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})


class MostSimilarAPIView(APIView):

    def get(self, request, format=None):
        cls = request.GET.get('class', None)
        size = request.GET.get('size', 50)
        ontology = request.GET.get('ontology', None)
        return self.process_query(cls, size, ontology)

    def process_query(self, cls, size, ontology):
        if cls is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide class parameter!'})
        if ontology is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide ontology parameter!'})
        try:
            size = int(size)
            query_list = [
                { 'term': { 'ontology': ontology } },
                { 'term': { 'class': cls } }
            ]
            docs = {
                'query': { 'bool': { 'must': query_list } },
            }
            result = search(ELASTIC_CLASS_INDEX_NAME, docs)
            data = result['hits']['hits']
            if len(data) == 0:
                return Response({'status': 'error', 'message': 'not found'})
            obj = data[0]['_source']
            encoded_vector = obj['embedding_vector']
            query = {
                "query": {
                    "function_score": {
                        "query": {"term": {"ontology": ontology}},
                        "boost_mode": "replace",
                        "script_score": {
                            "script": {
                                "inline": "binary_vector_score",
                                "lang": "knn",
                                "params": {
                                    "cosine": True,
                                    "field": "embedding_vector",
                                    "encoded_vector": encoded_vector
                                }
                            }
                        }
                    }
                },
                "_source": {"excludes": ["embedding_vector",]},
                "size": size
            }

            result = search(ELASTIC_CLASS_INDEX_NAME, query)
            data = []
            for hit in result['hits']['hits']:
                item = hit['_source']
                data.append(item)
            result = {'status': 'ok', 'result': data}
            return Response(result)
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})

    
class QueryOntologiesAPIView(APIView):

    def get(self, request, format=None):
        query = request.GET.get('query', None)

        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide query parameter!'})
        
        fields = ['name', 'ontology', 'description']
        query_list = []
        for field in fields:
            q = { 'match': { field: { 'query': query } } }
            query_list.append(q)
        omap = {
            'query': { 'bool': { 'should': query_list } },
            '_source': {'excludes': ['embedding_vector',]}
        }
        result = search(ELASTIC_ONTOLOGY_INDEX_NAME, omap)
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
            ('oboid', 10000),
            ('label', 1000),
            ('synonym', 100),
            ('ontology', 75),
            ('definition', 3),
        ]

        query_list = []

        omap = {}
        omap['dis_max'] = {}
        queries = [
            {'match': { 'oboid' : { 'query': query, 'boost': 10000 }}},
            {'match': { 'label' : { 'query': query, 'boost': 1000 }}},
            {'match': { 'synonym' : { 'query': query, 'boost': 100 }}},
            {'match': { 'ontology' : { 'query': query, 'boost': 100 }}},
            {'match': { 'definition' : { 'query': query, 'boost': 10 }}},
        ]
        omap['dis_max']['queries'] = queries
        query_list.append(omap)
        if ontology is not None:
            query_list.append({ 'match': { 'ontology': ontology } })

        f_query = {
            'query': { 'bool': { 'must': query_list } },
            '_source': {'excludes': ['embedding_vector',]},
            'from': 0,
            'size': 100}

        result = search(ELASTIC_CLASS_INDEX_NAME, f_query)
        data = defaultdict(list)
        for hit in result['hits']['hits']:
            item = hit['_source']
            data[item['owlClass']].append(item)
        ret = []
        for hit in result['hits']['hits']:
            owl_class = hit['_source']['owlClass']
            if owl_class in data:
                ret.append([owl_class, data[owl_class]])
                del data[owl_class]
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
                        result = r.json()
                        result['status'] = 'ok'
                        return Response(result)
                    else:
                        raise Exception('API server is down!')
                else:
                    raise Exception('Ontology does not exist!')
            else:
                queryset = Ontology.objects.filter(nb_servers__gt=0)
                if queryset.exists():
                    url = ABEROWL_API_URL + script + '?' + query_string
                    r = requests.get(url)
                    result = r.json()
                    result['status'] = 'ok'
                    return Response(result)
                else:
                    raise Exception('API server is down!')
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})
        
                

class OntologyListAPIView(ListAPIView):

    queryset = Ontology.objects.all()
    serializer_class = OntologySerializer
    

class ClassInfoAPIView(APIView):


    def __init__(self, *args, **kwargs):
        super(ClassInfoAPIView, self).__init__(*args, **kwargs)

    def post(self, request, format=None):
        ontology = request.POST.get('ontology', None)
        iris = request.POST.getlist('iri', None)
        print(request.POST)
        return self.process_query(iris, ontology)


    def get(self, request, format=None):
        ontology = request.GET.get('ontology', None)
        iris = request.GET.getlist('iri', None)
        return self.process_query(iris, ontology)

    def process_query(self, iris, ontology):
        if ontology is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide ontology!'})
        if iris is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide at least one IRI!'})
        try: 
            queryset = Ontology.objects.filter(acronym=ontology)
            if queryset.exists():
                ontology = queryset.get()
                if ontology.nb_servers:
                    result = {'status': 'ok', 'result': {}}
                    for query in iris:
                        params = {
                            'type': 'equivalent',
                            'direct': 'true',
                            'axioms': 'false',
                            'query': '<' + query + '>',
                            'ontology': ontology.acronym
                        }
                        url = ontology.get_api_url() + 'runQuery.groovy'
                        r = requests.get(url, params=params)
                        res = r.json()
                        if 'result' in res and len(res['result']) > 0:
                            for item in res['result']:
                                if item['class'] == query:
                                    result['result'][query] = item
                                    break
                    return Response(result)
                else:
                    raise Exception('API server is down!')
            else:
                raise Exception('Ontology does not exist!')
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})
        
class SparqlAPIView(APIView):

    def get(self, request, format=None):
        query = request.GET.get('query', None)
        try:
            return self.process_query(query)
        except KeyError:
            raise Exception("Malformed data!")

    def process_query(self, query):
        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide query element!'})
        try:
            url = ABEROWL_API_URL + 'sparql.groovy'
            print("URL" + url)
            r = requests.get(url, params = {'query': query})
            return HttpResponse(r.text)
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})