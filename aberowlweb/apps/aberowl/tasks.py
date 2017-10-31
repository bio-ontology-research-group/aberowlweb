from celery import task
from celery.task.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max
import requests
import shutil
from aberowl.models import Ontology, Submission
from subprocess import Popen, PIPE
import json
import random


BIOPORTAL_API_URL = getattr(
    settings, 'BIOPORTAL_API_URL', 'http://data.bioontology.org/')
BIOPORTAL_API_KEY = getattr(
    settings, 'BIOPORTAL_API_KEY', '24e0413e-54e0-11e0-9d7b-005056aa3316')
ABEROWL_API_URL = getattr(
    settings, 'ABEROWL_API_URL', 'http://localhost/')
ABEROWL_API_SERVERS_POOL = getattr(
    settings, 'ABEROWL_API_SERVERS_POOL', ['127.0.0.1'])


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
    metric_params = params.copy()
    metric_params['display'] = ('classes,individuals,properties,maxDepth'
                                + ',maxChildCount,averageChildCount')
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

            port = Ontology.objects.aggregate(Max('port'))['port__max'] or 10000
            port += 1
            server_ip = ABEROWL_API_SERVERS_POOL[random.randint(
                0, len(ABEROWL_API_SERVERS_POOL) - 1)]
            ontology, created = Ontology.objects.get_or_create(
                acronym=acronym,
                defaults={
                    'name': onto['name'],
                    'created_by': user,
                    'server_ip': server_ip,
                    'port': port,
                }
            )

            queryset = ontology.submissions.filter(
                submission_id=sub['submissionId'])
            if queryset.exists(): # Already uptodate
                submission = queryset.get()
                if not submission.indexed and submission.classifiable:
                    index_submission(ontology, submission)
                continue

            r = requests.get(
                BIOPORTAL_API_URL + 'ontologies/' + acronym + '/submissions/' +
                str(sub['submissionId']) + '/metrics',
                metric_params
            )
            metrics = {}
            if r.status_code == 200:
                metrics = r.json()
            print(acronym, metrics)
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
                version=sub['version'],
                nb_classes=metrics.get('classes', 0),
                nb_properties=metrics.get('properties', 0),
                nb_individuals=metrics.get('individuals', 0),
                max_depth=metrics.get('maxDepth', 0),
                max_children=metrics.get('maxChildCount', 0),
                avg_children=metrics.get('averageChildCount', 0)
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
                submission.save()
            else:
                print('Downloading ontology %s failed!' % (acronym,))
                continue

            p = Popen(
                ['groovy', 'Classify.groovy', '../' + submission.get_filepath()],
                stdout=PIPE,
                cwd='scripts/')
            if p.wait() == 0:
                output = p.stdout.readlines()
                print(output[-1].decode('utf-8'))
                result = json.loads(output[-1].decode('utf-8'))
                submission.nb_inconsistent = result['incon']
                submission.classifiable = result['classifiable']
                ontology.status = result['status']
                ontology.save()
            else:
                print('Classifying ontology %s failed!' % (acronym,))

            if not submission.classifiable:
                continue

            index_submission(ontology, submission)
        except Exception as e:
            print(acronym, e)


def index_submission(ontology, submission):
    p = Popen(
        ['groovy', 'IndexElastic.groovy', '../' + submission.get_filepath()],
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
    # Reloading ontology
    # r = requests.get(
    #     ABEROWL_API_URL + 'service/api/reloadOntology.groovy',
    #     params={'name': acronym})
