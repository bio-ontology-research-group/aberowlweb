import pytest
from django.db import connections

import psycopg2


def run_sql(sql):
    conn = psycopg2.connect(host="localhost", database='postgres',  user="postgres", password="111")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.yield_fixture(scope='session')
def django_db_setup():
    from django.conf import settings

    settings.DATABASES['default']['NAME'] = 'the_copied_db'

    run_sql('DROP DATABASE IF EXISTS the_copied_db')
    run_sql('CREATE DATABASE the_copied_db TEMPLATE aberowlweb')

    yield

    for connection in connections.all():
        connection.close()

    run_sql('DROP DATABASE the_copied_db')