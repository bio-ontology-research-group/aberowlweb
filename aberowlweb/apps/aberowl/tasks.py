from celery import task
from celery.task.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max
from django.utils import timezone
import requests
import shutil
from aberowl.models import Ontology, Submission
from subprocess import Popen, PIPE, DEVNULL
import json
import random
import os


BIOPORTAL_API_URL = getattr(
    settings, 'BIOPORTAL_API_URL', 'http://data.bioontology.org/')
BIOPORTAL_API_KEY = getattr(
    settings, 'BIOPORTAL_API_KEY', '24e0413e-54e0-11e0-9d7b-005056aa3316')

OBOFOUNDRY_API_URL = getattr(
    settings, 'OBOFOUNDRY_API_URL', 'http://obofoundry.org/')

ABEROWL_API_URL = getattr(
    settings, 'ABEROWL_API_URL', 'http://localhost:8080/api/')
ABEROWL_API_WORKERS = getattr(
    settings, 'ABEROWL_API_WORKERS', ['http://localhost:8080/api/'])
ABEROWL_SERVER_URL = getattr(
    settings, 'ABEROWL_SERVER_URL', 'http://localhost/')

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

@periodic_task(run_every=crontab(hour=12, minute=0, day_of_week=1))
def sync_obofoundry():
    user = User.objects.get(pk=1)
    timeout = 120
    params = {}
    try:
        r = requests.get(
            OBOFOUNDRY_API_URL + 'registry/ontologies.jsonld',
            params=params, timeout=timeout)
        if r.status_code != 200:
            print('Unable to load the list of ontologies')
            return

        data = r.json()
    except Exception as e:
        print(e)
        return

    for onto in data['ontologies']:
        acronym = onto['id'].upper()
        try:
            if 'is_obsolete' in onto and onto['is_obsolete']:
                continue

            ontology, created = Ontology.objects.get_or_create(
                acronym=acronym,
                defaults={
                    'name': onto['title'],
                    'created_by': user,
                    'source': Ontology.OBOFOUNDRY
                }
            )

            if ontology.source != Ontology.OBOFOUNDRY:
                ontology.source = Ontology.OBOFOUNDRY
                ontology.save()

            download_url = onto['ontology_purl']
            filedir = (settings.MEDIA_ROOT + 'ontologies/' + acronym + '/')
            if not os.path.exists(filedir):
                os.makedirs(filedir)
            filename = download_url.split('/')[-1]
            file_ext = filename.split('.')[1]
            filepath =  filedir + filename
            p = Popen(['curl', '-L', download_url, '-o', filepath])
            if p.wait() == 0:
                p = Popen(['md5sum', filepath], stdout=PIPE)
                if p.wait() == 0:
                    md5sum = p.stdout.read().strip().split()[0]
                    md5sum = md5sum.decode('utf-8')
                    print('MD5SUM:', md5sum)
                    p.stdout.close()
                    queryset = ontology.submissions.filter(md5sum=md5sum)
                    if queryset.exists(): # Already uptodate
                        continue
            else:
                print('Downloading ontology %s failed!' % (acronym,))
                continue
            
            submission_id = ontology.submissions.aggregate(
               Max('submission_id'))['submission_id__max'] or 0
            submission_id += 1
            
            submission = Submission(
                ontology=ontology,
                submission_id=submission_id,
                description=onto.get('description', ''),
                has_ontology_language=file_ext.upper(),
                date_released=timezone.now(),
                date_created=timezone.now(),
                home_page=onto.get('homepage', ''),
                publications=onto.get('publications', None),
                products=onto.get('products', None),
                taxon=onto.get('taxon', None),
                documentation=onto.get('documentation', None),
                domain=onto.get('domain', None),
                md5sum=md5sum,
            )
            
            shutil.move(filepath, submission.get_filepath())
            shutil.copyfile(
                submission.get_filepath(),
                submission.get_filepath(folder='latest'))

            filepath = '../' + submission.get_filepath()
            result = classify_ontology(filepath)
            if result['classifiable']:
                submission.nb_inconsistent = result['incon']
                submission.classifiable = result['classifiable']
                submission.nb_classes = result['nb_classes']
                submission.nb_properties = result['nb_properties']
                submission.nb_individuals = result['nb_individuals']
                submission.max_depth = result['max_depth']
                submission.max_children = result['max_children']
                submission.avg_children = result['avg_children']
                submission.save()
                ontology.status = result['status']
                ontology.save()
                ontIRI = ABEROWL_SERVER_URL + submission.get_filepath()
                reload_ontology.delay(ontology.acronym, ontIRI)
            else:
                print('Classifying ontology %s failed!' % (acronym,))

            if submission.classifiable:
                index_submission(ontology.pk, submission.pk)
            
        except Exception as e:
            print(acronym, e)

    
@periodic_task(run_every=crontab(hour=12, minute=0, day_of_week=2))
def sync_bioportal():
    user = User.objects.get(pk=1)
    params = {
        'apikey': BIOPORTAL_API_KEY,
        'format': 'json',
        'display_links': 'false',
        'display_context': 'false',
        'include_views': 'false',
        'display': 'acronym,name'
    }
    timeout = 120
    try:
        r = requests.get(
            BIOPORTAL_API_URL + 'ontologies/', params=params, timeout=timeout)
        if r.status_code != 200:
            print('Unable to load the list of ontologies')
            return

        data = r.json()
    except Exception as e:
        print(e)
        return

    params['display'] = (
        'hasOntologyLanguage,released,creationDate,homepage,status,' +
        'publication,documentation,version,description,submissionId')
    for onto in data:
        acronym = onto['acronym']
        try:
            r = requests.get(
                BIOPORTAL_API_URL + 'ontologies/' + acronym + '/latest_submission',
                params)
            if r.status_code != 200:
                print('Unable to load latest submission for %s' % (acronym,))
                continue
            sub = r.json()
            if sub.get('submissionId', None) is None or sub.get('status', None) == 'retired':
                continue

            ontology, created = Ontology.objects.get_or_create(
                acronym=acronym,
                defaults={
                    'name': onto['name'],
                    'created_by': user,
                    'source': Ontology.BIOPORTAL
                }
            )

            if ontology.source != Ontology.BIOPORTAL:
                continue

            queryset = ontology.submissions.filter(
                submission_id=sub['submissionId'])
            if queryset.exists(): # Already uptodate
                submission = queryset.get()
                if not submission.indexed and submission.classifiable:
                    index_submission(ontology.pk, submission.pk)
                continue

            submission = Submission(
                ontology=ontology,
                submission_id=sub['submissionId'],
                description=sub['description'],
                has_ontology_language=sub['hasOntologyLanguage'],
                date_released=sub['released'],
                date_created=sub['creationDate'],
                home_page=sub['homepage'],
                publication=sub['publication'],
                documentation=sub['documentation'],
                version=sub['version']
            )
            download_url = (BIOPORTAL_API_URL + 'ontologies/' + acronym
                        + '/download?apikey=' + BIOPORTAL_API_KEY)
            filepath = submission.get_filepath() + '.donwload'
            p = Popen(['curl', '-L', download_url, '-o', filepath])
            if p.wait() == 0:
                shutil.move(filepath, submission.get_filepath())
                shutil.copyfile(
                    submission.get_filepath(),
                    submission.get_filepath(folder='latest'))
            else:
                print('Downloading ontology %s failed!' % (acronym,))
                continue
            filepath = '../' + submission.get_filepath()
            result = classify_ontology(filepath)
            if result['classifiable']:
                submission.nb_inconsistent = result['incon']
                submission.classifiable = result['classifiable']
                submission.nb_classes = result['nb_classes']
                submission.nb_properties = result['nb_properties']
                submission.nb_individuals = result['nb_individuals']
                submission.max_depth = result['max_depth']
                submission.max_children = result['max_children']
                submission.avg_children = result['avg_children']
                submission.save()
                ontology.status = result['status']
                ontology.save()
                ontIRI = ABEROWL_SERVER_URL + submission.get_filepath()
                reload_ontology.delay(ontology.acronym, ontIRI)
            else:
                print('Classifying ontology %s failed!' % (acronym,))

            if submission.classifiable:
                index_submission(ontology.pk, submission.pk).delay()
            
        except Exception as e:
            print(acronym, e)


@task
def classify_ontology(filepath):
    p = Popen(
        ['groovy', 'Classify.groovy', filepath],
        cwd='scripts/', stderr=DEVNULL, stdout=PIPE)
    if p.wait() == 0:
        lines = p.stdout.readlines()
        result = json.loads(lines[-1].decode('utf-8'))
        return result
    return {'classifiable': False}


@task
def index_submission(ontology_pk, submission_pk, skip_embedding = True, es_url=ELASTIC_SEARCH_URL, 
                        es_username=ELASTIC_SEARCH_USERNAME, es_password=ELASTIC_SEARCH_PASSWORD):
    ontology = Ontology.objects.get(pk=ontology_pk)
    submission = ontology.submissions.get(pk=submission_pk)
    filepath = '../' + submission.get_filepath(folder='latest')
    if not skip_embedding:
        generate_embeddings(filepath)

    p = Popen(
        ['groovy', 'IndexElastic.groovy', es_url, es_username, es_password,
        ELASTIC_ONTOLOGY_INDEX_NAME,  ELASTIC_CLASS_INDEX_NAME, filepath, str(skip_embedding)],
        stdin=PIPE,
        cwd='scripts/')
    data = {
        'acronym': ontology.acronym,
        'name': ontology.name,
        'description': submission.description
    }
    p.stdin.write(json.dumps(data).encode('utf-8'))
    p.stdin.close()

    if p.wait() == 0:
        print('Indexing ontology %s finished' % (ontology.acronym))
        submission.indexed = True
    else:
        print('Indexing ontology %s failed!' % (ontology.acronym))

    submission.save()

@task
def reload_ontology(ont, ontIRI):
    for api_worker_url in ABEROWL_API_WORKERS:
        print('Running request: ', api_worker_url)
        r = requests.get(
            api_worker_url + 'reloadOntology.groovy',
            params={'ontology': ont, 'ontologyIRI': ontIRI})
        print(r.json())

@task
def generate_embeddings(filepath):
    p = Popen(
        ['groovy', 'Axioms.groovy', filepath],
        cwd='scripts/', stderr=DEVNULL, stdout=PIPE)
    result = {'classifiable': False}
    if p.wait() == 0:
        lines = p.stdout.readlines()
        result = json.loads(lines[-1].decode('utf-8'))
    if not result['classifiable']:
        return result
    p = Popen(
        ['word2vec', '-train', (filepath + '.axms'),
         '-output', (filepath + '.embs'), '-size', '256',
         '-min-count', '1', '-iter', '50'],
        cwd='scripts/', stderr=DEVNULL, stdout=DEVNULL)
    if p.wait() == 0:
        print('Successfully generated embeddings for ', filepath)
    return result


@task
def reload_indexes(skip_embedding, es_url=ELASTIC_SEARCH_URL, es_username=ELASTIC_SEARCH_USERNAME, es_password=ELASTIC_SEARCH_PASSWORD):
    try: 
        ontologies =  Ontology.objects.filter(
            status=Ontology.CLASSIFIED)
        for ontology in ontologies :
            for submission in ontology.submissions.all() :
                print('Indexing ontology %s started' % (ontology.acronym))
                index_submission(ontology.pk, submission.pk, skip_embedding, es_url, es_username, es_password)

    except Exception as e:
            print(e)

@task
def reload_index(ontology_acronym):
    try: 
        ontologies =  Ontology.objects.filter(
            acronym=ontology_acronym, status=Ontology.CLASSIFIED)
        if len(ontologies) > 0:
            for submission in ontologies[0].submissions.all() :
                print('Indexing ontology %s started' % (ontologies[0].acronym))
                index_submission(ontologies[0].pk, submission.pk)

    except Exception as e:
            print(e)