from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from aberowl.models import Ontology
import random


class Command(BaseCommand):
    help = 'Assign ontlogies to worker servers'

    def add_arguments(self, parser):
        parser.add_argument('server_ip', type=str)
        parser.add_argument('nb', type=int)

    def handle(self, *args, **options):
        server_ip = options['server_ip']
        nb = options['nb']
        onts = Ontology.objects.filter(
            status=Ontology.CLASSIFIED,
            server_ip='127.0.0.1')
        n = len(onts)
        if nb > n:
            nb = n
        ids = random.sample(range(n), nb)
        for i in ids:
            onts[i].server_ip = server_ip
            onts[i].save()

        print('Total number of idle ontologies %d' % (len(onts),))
