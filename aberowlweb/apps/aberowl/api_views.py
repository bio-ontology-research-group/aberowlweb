from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from urllib import parse

import coreapi
import requests
import json
import itertools

from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.conf import settings
from django.shortcuts import redirect
from collections import defaultdict
from gevent.pool import Pool
import time

from aberowlweb.apps.aberowl.ont_server_request_processor import OntServerRequestProcessor
from aberowl.models import Ontology
from aberowl.serializers import OntologySerializer
from elasticsearch import Elasticsearch

from django.core.paginator import Paginator
from expiringdict import ExpiringDict

import logging

logger = logging.getLogger(__name__)

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

class FindClassByMethodStartWithAPIView(APIView):

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

class FindClassAPIView(APIView):

    def get(self, request, format=None):
        
        query = request.GET.get('query', None)
        ontology = request.GET.get('ontology', None)
        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'Please provide query parameter!'})

        queries = [
            {'match': { 'oboid' : { 'query': query, 'boost': 150 }}},
            {'match': { 'label' : { 'query': query, 'boost': 100 }}},
            {'match': { 'synonym' : { 'query': query, 'boost': 50 }}},
            {'match': { 'definition' : { 'query': query, 'boost': 30 }}},
        ]
        if ontology is not None:
            queries.append({ 'match': { 'ontology': ontology, "boost":500 } })
        else:
            queries.append({ 'terms': { 'ontology' : query.lower().split(), 'boost': 150 }})

        f_query = {
            'query': { 'bool': { 'should': queries } },
            '_source': {'excludes': ['embedding_vector',]},
            'from': 0,
            'size': 100}
            
        logger.info("Executing query:" + str(f_query))

        result = search(ELASTIC_CLASS_INDEX_NAME, f_query)
        # data = defaultdict(list)
        # for hit in result['hits']['hits']:
        #     item = hit['_source']
        #     data[item['owlClass']].append(item)
        # ret = []
        # for hit in result['hits']['hits']:
        #     owl_class = hit['_source']['owlClass']
        #     if owl_class in data:
        #         ret.append([owl_class, data[owl_class]])
        #         del data[owl_class]
        data = []
        for hit in result['hits']['hits']:
            item = hit['_source']
            data.append(item)
        result = {'status': 'ok', 'result': data}
        return Response(result)

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



# This API is depricated there is API defined for aberowl knowledge graph functions.
class BackendAPIView(APIView):

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
        

class FindOntologyAPIView(APIView):

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

class ListOntologyAPIView(ListAPIView):
    """
    get: Returns the list of all ontologies in aberowl
    """

    queryset = Ontology.objects.all()
    serializer_class = OntologySerializer
        
class SparqlAPIView(APIView):

    def get(self, request, format=None):
        query = request.GET.get('query', None)
        res_format = request.GET.get('result_format', None)
        try:
            return self.process_query(query, res_format)
        except KeyError:
            raise Exception("Malformed data!")

    def process_query(self, query, res_format):
        if query is None:
            return Response(
                {'status': 'error',
                 'message': 'query is required'})
        if res_format is None:
            return Response(
                {'status': 'error',
                 'message': 'result format is required'})
        try:
            url = ABEROWL_API_URL + 'sparql.groovy'
            logger.debug("URL:" + url)
            response = requests.get(url, params = {'query': query})
            if response.status_code == 400:
                return HttpResponse(response.text)
            if response.status_code == 200:
                content = response.json()
                query_url="{endpoint}?query={query}&format={res_format}&timeout=0&debug=on&run={run}"\
                    .format(endpoint=content['endpoint'], query=parse.quote(content['query']), res_format=parse.quote(res_format), 
                    run=parse.quote('Run Query'))
                
                logger.debug("redirect to:" + query_url)
                response = HttpResponseRedirect(redirect_to=query_url)
                return response
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
        direct = request.GET.get('direct', True)
        
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
                result = ont_server.execute_dl_query(query, query_type, ontology, axioms, labels, direct)
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

class ListOntologyObjectPropertiesView(APIView):
    def get(self, request, acronym):
        try:
            result = ont_server.find_ontology_object_properties(acronym)
            result['status'] = 'ok'
            result['total'] = len(result['result'])
            return Response(result)
                
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})


class GetOntologyObjectPropertyView(APIView):
    def get(self, request, acronym, property_iri):
        try:
            result = ont_server.find_ontology_object_properties(acronym, property_iri)
            result['status'] = 'ok'
            return Response(result)
                
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})

class GetOntologyClassView(APIView):

    def __init__(self, *args, **kwargs):
        super(GetOntologyClassView, self).__init__(*args, **kwargs)

    def post(self, request, acronym, class_iri):
        return self.process_query(class_iri, acronym)


    def get(self, request, acronym, class_iri):
        return self.process_query(class_iri, acronym)

    def process_query(self, iri, ontology):
        try: 
            queryset = Ontology.objects.filter(acronym=ontology)
            if queryset.exists():
                ontology = queryset.get()
                if ontology.nb_servers:
                    result = {'status': 'ok', 'result': {}}
                    params = {
                        'type': 'equivalent',
                        'direct': 'true',
                        'axioms': 'false',
                        'query': '<' + iri + '>',
                        'ontology': ontology.acronym
                    }
                    url = ontology.get_api_url() + 'runQuery.groovy'
                    r = requests.get(url, params=params)
                    res = r.json()
                    if 'result' in res and len(res['result']) > 0:
                        for item in res['result']:
                            if item['class'] == iri:
                                result['result'][query] = item
                    return Response(result)
                else:
                    raise Exception('API server is down!')
            else:
                raise Exception('Ontology does not exist!')
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})


class FindOntologyRootClassView(APIView):
    def get(self, request, acronym, class_iri):
        try:
            result = ont_server.find_ontology_root(class_iri, acronym)
            result['status'] = 'ok'
            result['total'] = len(result['result'])
            return Response(result)
                
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})

class ListInstanceAPIView(APIView):
    def get(self, request):
        ontology = request.GET.get('ontology', None)
        class_iri = request.GET.get('class_iri', None)

        if ontology is None:
            return Response({'status': 'error', 'message': 'ontology acronym is required'})
        if class_iri is None:
            return Response({'status': 'error', 'message': 'class_iri is required'})
        print(ontology, class_iri)
        try:
            result = ont_server.find_by_ontology_and_class(ontology, class_iri)
            return Response(result)
                
        except Exception as e:
            return Response({'status': 'exception', 'message': str(e)})
