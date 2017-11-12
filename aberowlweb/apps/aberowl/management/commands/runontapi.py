from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import F
from aberowl.models import Ontology

from gevent.subprocess import Popen, PIPE
import time
import signal
import logging
import gevent
import json

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
        self.proc = Popen(
            ['groovy', 'OntologyServer.groovy'],
            cwd='aberowlapi/', stdin=PIPE, stdout=PIPE, universal_newlines=True)
        self.proc.stdin.write(data)
        self.proc.stdin.close()
        for line in self.proc.stdout:
            line = line.strip()
            logging.info(line)
            if line.startswith('Finished loading'):
                oid = line.split()[2]
                if oid not in self.loaded:
                    self.loaded.add(oid)
                    Ontology.objects.filter(
                        acronym=oid).update(nb_servers=F('nb_servers') + 1)
                    
        self.proc.stdout.close()
        self.proc.wait()
