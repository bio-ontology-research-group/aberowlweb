from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import F
from aberowl.models import Ontology
from django import db

from gevent.subprocess import Popen, PIPE
import time
import signal
import logging
import gevent
import json
import os

ABEROWL_SERVER_URL = getattr(settings, 'ABEROWL_SERVER_URL', 'http://localhost/')

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = 'Starts API servers for all ontologies'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.processes = {}
        signal.signal(signal.SIGTERM, self.stop_subprocesses)
        signal.signal(signal.SIGINT, self.stop_subprocesses)
        signal.signal(signal.SIGQUIT, self.stop_subprocesses)

    def add_arguments(self, parser):
        pass
    
    def stop_subprocesses(self, signum, frame):
        if self.proc.poll() is None:
            self.proc.kill()
        Ontology.objects.filter(
            nb_servers__gt=0,
            acronym__in=self.loaded).update(nb_servers=F('nb_servers') - 1)
        exit(0)
                
    def handle(self, *args, **options):
        ontologies = Ontology.objects.filter(
            status=Ontology.CLASSIFIED)
        data = []
        self.loaded = set()
        for ont in ontologies:
            ontIRI = ABEROWL_SERVER_URL + ont.get_latest_submission().get_filepath()
            data.append({'ontId': ont.acronym, 'ontIRI': ontIRI})
        data = json.dumps(data)
        env = os.environ.copy()
        env['JAVA_OPTS'] = '-Xmx128g -Xms8g -XX:+UseParallelGC'
        self.proc = Popen(
            ['groovy', 'OntologyServer.groovy'],
            cwd='aberowlapi/', stdin=PIPE, stdout=PIPE,
            universal_newlines=True, env=env)
        self.proc.stdin.write(data)
        self.proc.stdin.close()
        for line in self.proc.stdout:
            line = line.strip()
            logging.info(line)
            if line.startswith('Finished loading'):
                oid = line.split()[2]
                if oid not in self.loaded:
                    self.loaded.add(oid)
                    try:                
                        Ontology.objects.filter(
                            acronym=oid).update(nb_servers=F('nb_servers') + 1)
                    except Exception as e:
                        print('Exception:', e)
                        # Reset database connection if update query fails
                        db.close_connection() 
                        Ontology.objects.filter(
                            acronym=oid).update(nb_servers=F('nb_servers') + 1)
            if line.startswith('Unloadable ontology'):
                oid = line.split()[2]
                try:                
                    Ontology.objects.filter(acronym=oid).update(status=Ontology.UNLOADABLE)
                except Exception as e:
                        print('Exception:', e)
        self.proc.stdout.close()
        self.proc.wait()
