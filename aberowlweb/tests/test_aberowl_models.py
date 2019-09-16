import pytest
from aberowl.models import Ontology, Submission 
from django.contrib.auth.models import User
import datetime

@pytest.mark.django_db
def test_create_ontology():
    # given
    date = datetime.datetime(2019,9,13)
    date_str = date.strftime('%Y-%m-%d %H:%M')
    status = Ontology.STATUS_CHOICES[0][0]
    user = User.objects.create_user('user1', 'user1@test.com', 'user')

    # when
    ontology = Ontology.objects.create(acronym="edam", name="edam ontology", source="bioportal", created_by=user, 
            date_modified=date_str, status=status)
    # then
    assert ontology.acronym == "edam"
    assert ontology.name == "edam ontology"
    assert ontology.source == "bioportal"
    assert ontology.date_modified == date_str
    assert ontology.status == Ontology.STATUS_CHOICES[0][0]
    assert ontology.is_obsolete == False
    assert ontology.nb_servers == 0

@pytest.mark.django_db
def test_create_submission():
    # given
    date = datetime.datetime(2019,9,13)
    date_str = date.strftime('%Y-%m-%d %H:%M')
    status = Ontology.STATUS_CHOICES[0][0]
    user = User.objects.create_user('user1', 'user1@test.com', 'user')
    ontologyRef = Ontology.objects.create(acronym="edam", name="edam ontology", source="bioportal", created_by=user, 
        date_modified=date_str, status=status)

    # when
    submission = Submission.objects.create(submission_id="1", ontology=ontologyRef, domain="biology", description="some desc", 
        date_released=date_str, date_created=date_str, version="1.0", nb_classes=100, indexed=False)

    # then
    assert submission.submission_id == "1"
    assert submission.ontology.pk == ontologyRef.pk
    assert submission.domain == "biology"
    assert submission.description == "some desc"
    assert submission.date_released == date_str
    assert submission.date_created == date_str
    assert submission.version == "1.0"
    assert submission.nb_classes == 100
    assert submission.indexed == False
