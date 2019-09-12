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
        parser.add_argument('-u', '--elasticsearch_username', type=str, help='elasticsearch user name', )
        parser.add_argument('-p', '--elasticsearch_password', type=str, help='elasticsearch password', )
    
    def stop_subprocesses(self, signum, frame):
        if self.proc.poll() is None:
            self.proc.kill()
        exit(0)
                
    def handle(self, *args, **options):
        es_url = options['elasticsearch_url']
        es_username = options['elasticsearch_username']
        es_password = options['elasticsearch_password']
        if  es_username and es_password:
            reload_indexes(True, es_url, es_username, es_password)
        else:
            reload_indexes(True, es_url)