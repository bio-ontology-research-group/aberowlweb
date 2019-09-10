from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from aberowl.models import Ontology

from aberowl.tasks import reload_indexes

import signal
import logging

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = 'Starts reloading all the ontology indexes for target elastic search server'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.processes = {}
        signal.signal(signal.SIGTERM, self.stop_subprocesses)
        signal.signal(signal.SIGINT, self.stop_subprocesses)
        signal.signal(signal.SIGQUIT, self.stop_subprocesses)

    def add_arguments(self, parser):
        parser.add_argument('elasticsearch_url', type=str, help='elasticsearch server')
    
    def stop_subprocesses(self, signum, frame):
        if self.proc.poll() is None:
            self.proc.kill()
        exit(0)
                
    def handle(self, *args, **options):
        elasticsearch_url = options['elasticsearch_url']
        reload_indexes(skip_embedding = True, es_url=elasticsearch_url)
