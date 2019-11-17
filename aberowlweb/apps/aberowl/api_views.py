from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import schemas
from urllib import parse

import coreapi
import requests
import json
import itertools

from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.conf import settings
from collections import defaultdict
from gevent.pool import Pool
import time

from aberowlweb.apps.aberowl.ont_server_request_processor import OntServerRequestProcessor
from aberowl.models import Ontology
from aberowl.serializers import OntologySerializer
from elasticsearch import Elasticsearch

from django.core.paginator import Paginator
from expiringdict import ExpiringDict


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

LOG_FOLDER = getattr(
    settings, 'DLQUERY_LOGS_FOLDER', 'logs')

DEFUALT_PAGE_SIZE = 10
page_cache = ExpiringDict(max_len=100, max_age_seconds=3600)
ont_server = OntServerRequestProcessor()

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

    schema = schemas.ManualSchema(fields=[
                    coreapi.Field(
                        name='query',
                        location='query',
                        required=True,
                        type='string',
                        description='query may contain text that contains name of the class or part of class name'
                    ),
                    coreapi.Field(
                        name='ontology',
                        location='query',
                        required=True,
                        type='string',
                        description='ontology acronym to search classes in a given ontology'
                    )
                ], description="API for searching a class in an ontology for given text which can be full name of the class or a part of it")

    def get(self, request, format=None):
        query = request.GET.get('query', None)
        ontology = request.GET.get('ontology', None)
        return self.process_query(query, ontology)

    def process_query(self, query, ontology):
        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'query is required'})
        if ontology is None:
            return Response(
                {'status': 'error',
                 'message': 'ontology is required'})
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

    schema = schemas.ManualSchema(description="Search API for finding most similar classes of a given class in an ontology",
                fields=[
                    coreapi.Field(
                        name='ontology',
                        location='query',
                        required=True,
                        type='string',
                        description='ontology acronym'
                    ),
                    coreapi.Field(
                        name='class',
                        location='query',
                        required=True,
                        type='string',
                        description='name of the class'
                    ),
                    coreapi.Field(
                        name='size',
                        location='query',
                        required=False,
                        type='string',
                        description='number of most similar classes to be fetched. By default, the size is 50.'
                    )
                ])

    def get(self, request, format=None):
        cls = request.GET.get('class', None)
        size = request.GET.get('size', 50)
        ontology = request.GET.get('ontology', None)
        return self.process_query(cls, size, ontology)

    def process_query(self, cls, size, ontology):
        if cls is None:
            return Response(
                {'status': 'error',
                 'message': 'class is required'})
        if ontology is None:
            return Response(
                {'status': 'error',
                 'message': 'ontology is required'})
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

    schema = schemas.ManualSchema(description="Search API for ontologies in aberowl repository for given text.",
                fields=[
                    coreapi.Field(
                        name='query',
                        location='query',
                        required=True,
                        type='string',
                        description='query may contain name of the ontology, acronym of the ontology or text part of ontology description'
                    )
                ])

    def get(self, request, format=None):
        query = request.GET.get('query', None)

        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'query field is required'})
        
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

    schema = schemas.ManualSchema(description="Search API for ontology classes in aberowl repository for given search criteria.",
                fields=[
                    coreapi.Field(
                        name='query',
                        location='query',
                        required=True,
                        type='string',
                        description='query may contain text that contains name, synonym, and oboid of the class'
                    ),
                    coreapi.Field(
                        name='ontology',
                        location='query',
                        required=False,
                        type='string',
                        description='ontology acronym to search classes in a given ontology'
                    )
                ])

    def get(self, request, format=None):
        
        query = request.GET.get('query', None)
        ontology = request.GET.get('ontology', None)
        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide query parameter!'})

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

    schema = schemas.ManualSchema(description="Multi function API for executing different functions on aberowl knowledge graph including executing DL query, finding root class in an ontology and getting object properties of an ontology",
                fields=[
                    coreapi.Field(
                        name='script',
                        location='query',
                        required=True,
                        type='string',
                        description='functions to be performed on aberowl knowledge base include findRoot.groovy, runQuery.groovy and getObjectProperties.groovy'
                    ),
                    coreapi.Field(
                        name='query',
                        location='query',
                        required=False,
                        type='string',
                        description='DL query to be executed'
                    ),
                    coreapi.Field(
                        name='type',
                        location='query',
                        required=False,
                        type='string',
                        description='Type of DL query includes subclass, subeq, equivalent, superclass and supeq'
                    ),
                    coreapi.Field(
                        name='ontology',
                        location='query',
                        required=False,
                        type='string',
                        description='ontology acronym'
                    ),
                    coreapi.Field(
                        name='offset',
                        location='query',
                        required=False,
                        type='string',
                        description='page number if given will return a page with 10 results by default'
                    )
                ])

    def __init__(self, *args, **kwargs):
        super(BackendAPIView, self).__init__(*args, **kwargs)
    

    def get(self, request, format=None):
        query_string = request.GET.urlencode()
        query = request.GET.get('query', None)
        query_type = request.GET.get('type', None)
        ontology = request.GET.get('ontology', None)
        script = request.GET.get('script', None)
        offset = request.GET.get('offset', None)

        if script is None:
            return Response(
                {'status': 'error',
                 'message': 'script is required'})
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
                        result['total'] = len(result['result'])
                        return Response(result)
                    else:
                        raise Exception('API server is down!')
                else:
                    raise Exception('Ontology does not exist!')
            elif ontology is None and script == 'runQuery.groovy' and query is not None and query_type is not None and offset is not None:
                pages_key = query + ":" + query_type
                if page_cache.get(pages_key):
                    result = { 'status' : 'ok'}
                    result['result'] = page_cache.get(pages_key).page(offset).object_list
                    result['total'] = page_cache.get(pages_key).count
                    return Response(result)
                else :
                    queryset = Ontology.objects.filter(nb_servers__gt=0)
                    if queryset.exists():
                        url = ABEROWL_API_URL + script + '?' + query_string
                        r = requests.get(url)
                        result = r.json()
                        page_cache[pages_key] = Paginator(result['result'], DEFUALT_PAGE_SIZE)
                        result['result'] = page_cache.get(pages_key).page(offset).object_list
                        result['total'] = page_cache.get(pages_key).count
                        result['status'] = 'ok'
                        return Response(result)
                    else:
                        raise Exception('API server is down!')
            else:
                queryset = Ontology.objects.filter(nb_servers__gt=0)
                if queryset.exists():
                    url = ABEROWL_API_URL + script + '?' + query_string
                    r = requests.get(url)
                    result = r.json()
                    result['status'] = 'ok'
                    result['total'] = len(result['result'])
                    return Response(result)
                else:
                    raise Exception('API server is down!')
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})
        

class OntologyListAPIView(ListAPIView):
    """
    get: Returns the list of all ontologies in aberowl
    """

    queryset = Ontology.objects.all()
    serializer_class = OntologySerializer

class CustomClassInfoAPISchema(schemas.AutoSchema):
    def __init__(self, description=''):
        self._description=description
    
    """
    Overrides `get_link()` to provide Custom Behavior X
    """
    def get_link(self, path, method, base_url):
        # link = super().get_link(path, method, base_url)
        encoding=None
        fields=[]
        if method=='GET':
            fields = [
                    coreapi.Field(
                        name='ontology',
                        location='query',
                        required=True,
                        type='string',
                    ),
                    coreapi.Field(
                        name='iri',
                        location='query',
                        required=True,
                        type='string'
                    )
                ]
        elif method=='POST':
            fields = [
                    coreapi.Field(
                        name='ontology',
                        location='form',
                        required=True,
                        type='string'
                    ),
                    coreapi.Field(
                        name='iri',
                        location='form',
                        required=True,
                        type='string'
                    )
                ]
            encoding = "application/x-www-form-urlencoded"
        if base_url and path.startswith('/'):
            path = path[1:]

        return coreapi.Link(
            url=parse.urljoin(base_url, path),
            action=method.lower(),
            encoding=encoding,
            fields=fields,
            description=self._description
        )
        
class ClassInfoAPIView(APIView):

    schema = CustomClassInfoAPISchema("""Search API for ontology class objects in aberowl based on ontology acronym and 
        class iris. Returns a list of classes for given ontology and class iris""")

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
                 'message': 'ontoglogy is required'})
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
    schema = schemas.ManualSchema(description="Executes the given aberowl SPARQL query and returns the results of the query in json format",
                fields=[
                    coreapi.Field(
                        name='query',
                        location='query',
                        required=True,
                        type='string',
                        description='the aberowl SPARQL query field'
                    )
                ])

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
                 'message': 'query is required'})
        try:
            url = ABEROWL_API_URL + 'sparql.groovy'
            print("URL" + url)
            r = requests.get(url, params = {'query': query})
            return HttpResponse(r.text)
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})


class DLQueryAPIView(APIView):

    def get(self, request, format=None):
        query = request.GET.get('query', None)
        query_type = request.GET.get('type', None)
        ontology = request.GET.get('ontology', None)
        axioms = request.GET.get('axioms', None)
        labels = request.GET.get('labels', None)
        offset = request.GET.get('offset', None)

        if query is None:
            return Response({'status': 'error', 'message': 'query is required'})
        if query_type is None:
            return Response({'status': 'error', 'message': 'type is required'})

        try: 
            if ontology is None and offset is not None:
                pages_key = query + ":" + query_type
                if page_cache.get(pages_key):
                    result = { 'status' : 'ok'}
                    result['result'] = page_cache.get(pages_key).page(offset).object_list
                    result['total'] = page_cache.get(pages_key).count
                    return Response(result)
                
                else:
                    result = ont_server.execute_dl_query(query, query_type, None, axioms, labels)
                    page_cache[pages_key] = Paginator(result['result'], DEFUALT_PAGE_SIZE)
                    result['result'] = page_cache.get(pages_key).page(offset).object_list
                    result['total'] = page_cache.get(pages_key).count
                    result['status'] = 'ok'
                    return Response(result)
            else:     
                result = ont_server.execute_dl_query(query, query_type, ontology, axioms, labels)
                result['status'] = 'ok'
                result['total'] = len(result['result'])
                return Response(result)
                
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})
        

class DLQueryLogsDownloadAPIView(APIView):

    def get(self, request, format=None):
        filename = 'aberowl-dl-logs.txt'
        file_path = '{log_folder}/{filename}'.format(log_folder=LOG_FOLDER, filename=filename)
        try :
            FilePointer = open(file_path,"r")
            response = HttpResponse(FilePointer,content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename=' + filename
            return response
        except FileNotFoundError as e:
            return HttpResponseNotFound()
