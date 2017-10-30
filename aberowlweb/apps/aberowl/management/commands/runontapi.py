from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from aberowl.models import Ontology
from subprocess import Popen, PIPE
import time
import logging
import gevent

ABEROWL_SERVER_URL = getattr(settings, 'ABEROWL_SERVER_URL', 'http://localhost/')

logging.basicConfig(level=logging.INFO)


def processInThread(proc, oid):

    def runInThread(proc, oid):
        for line in proc.stdout:
            line = line.strip()
            logging.info(line)
            if line == 'Finished loading ' + oid:
                Ontology.objects.filter(
                    acronym=oid).update(is_running=True)
        proc.stdout.close()
        proc.wait()
        logging.info('API Server for %s has been stopped' % (oid, ))
        Ontology.objects.filter(acronym=oid).update(is_running=False)

    g = gevent.spawn(runInThread, proc, oid)
    # returns immediately after the thread starts
    return g        

class Command(BaseCommand):
    help = 'Starts API servers for all ontologies'

    def add_arguments(self, parser):
        parser.add_argument('server_ip', type=str)

    def handle(self, *args, **options):
        server_ip = options['server_ip']
        self.processes = {}
        while True:
            try: 
                ontologies = Ontology.objects.filter(
                    status=Ontology.CLASSIFIED,
                    is_running=False,
                    server_ip=server_ip, acronym__in=['SIO', 'AGRO', 'IDO'])
                print('Ontologies', len(ontologies))
                for ontology in ontologies:
                    oid = ontology.acronym
                    if oid not in self.processes:
                        logging.info(
                            'Starting API for %s on server %s port %d' % (
                            oid, server_ip, ontology.port))
                        ontIRI = ABEROWL_SERVER_URL + ontology.get_latest_submission().get_filepath()
                        proc = Popen(
                            ['groovy', 'OntologyServer.groovy', oid, ontIRI,
                             str(ontology.port)],
                            cwd='aberowlapi/', stdout=PIPE, universal_newlines=True)
                        self.processes[oid] = proc
                        processInThread(proc, oid)
                        time.sleep(30)
                    else:
                        proc = self.processes[oid]
                        if proc.poll() is not None:
                            del self.processes[oid]
                        
                else:
                    if len(self.processes) == 0:
                        logging.info('No ontologies assigned to this server')
                time.sleep(60)
            except KeyboardInterrupt:
                for oid, p in self.processes.items():
                    if p.poll() is None:
                        logging.info('Stopping API for %s' % (oid, ))
                        p.kill()
                break
            
