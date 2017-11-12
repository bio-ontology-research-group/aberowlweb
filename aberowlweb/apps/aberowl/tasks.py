from celery import task
from celery.task.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max
import requests
import shutil
from aberowl.models import Ontology, Submission
from subprocess import Popen, PIPE, DEVNULL
import json
import random


BIOPORTAL_API_URL = getattr(
    settings, 'BIOPORTAL_API_URL', 'http://data.bioontology.org/')
BIOPORTAL_API_KEY = getattr(
    settings, 'BIOPORTAL_API_KEY', '24e0413e-54e0-11e0-9d7b-005056aa3316')
ABEROWL_API_URL = getattr(
    settings, 'ABEROWL_API_URL', 'http://localhost:8080/api/')
ABEROWL_API_WORKERS = getattr(
    settings, 'ABEROWL_API_WORKER_URLS', ['http://localhost:8080/api/'])
ABEROWL_SERVER_URL = getattr(
    settings, 'ABEROWL_SERVER_URL', 'http://localhost/')

ELASTIC_SEARCH_URL = getattr(
    settings, 'ELASTIC_SEARCH_URL', 'http://localhost:9200/')


@periodic_task(run_every=crontab(hour=12, minute=0))
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
                }
            )

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
def index_submission(ontology_pk, submission_pk):
    ontology = Ontology.objects.get(pk=ontology_pk)
    submission = ontology.submissions.get(pk=submission_pk) 
    p = Popen(
        ['groovy', 'IndexElastic.groovy',
         ELASTIC_SEARCH_URL, '../' + submission.get_filepath()],
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
    
