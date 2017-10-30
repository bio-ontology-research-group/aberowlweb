from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from aberowl.models import Ontology
from gevent.subprocess import Popen, PIPE
import time
import signal
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

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.processes = {}
        signal.signal(signal.SIGTERM, self.stop_subprocesses)
        signal.signal(signal.SIGINT, self.stop_subprocesses)
        signal.signal(signal.SIGQUIT, self.stop_subprocesses)

    def add_arguments(self, parser):
        parser.add_argument('server_ip', type=str)

    def stop_subprocesses(self, signum, frame):
        for oid, p in self.processes.items():
            if p.poll() is None:
                logging.info('Stopping API for %s' % (oid, ))
                p.kill()
                Ontology.objects.filter(acronym=oid).update(is_running=False)
        exit(0)
                
    def handle(self, *args, **options):
        server_ip = options['server_ip']
        
        while True:
            ontologies = Ontology.objects.filter(
                status=Ontology.CLASSIFIED,
                is_running=False,
                server_ip=server_ip)
            print('Ontologies', len(ontologies))
            threads = []
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
                    g = processInThread(proc, oid)
                    g.start()
                else:
                    proc = self.processes[oid]
                    if proc.poll() is not None:
                        del self.processes[oid]

            else:
                if len(self.processes) == 0:
                    logging.info('No ontologies assigned to this server')
            gevent.sleep(60)

