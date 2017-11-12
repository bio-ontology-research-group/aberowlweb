from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from aberowl import manage_views as views

urlpatterns = [
    url(r'^ontology/$',
        login_required(views.MyOntologyListView.as_view()),
        name='list_ontology'),
    url(r'^ontology/create/$',
        login_required(views.OntologyCreateView.as_view()),
        name='create_ontology'),
    url(r'^ontology/edit/(?P<pk>\d+)$',
        login_required(views.OntologyUpdateView.as_view()),
        name='edit_ontology'),
    url(r'^ontology/(?P<onto_pk>\d+)/submission/create/$',
        login_required(views.SubmissionCreateView.as_view()),
        name='create_submission'),
    url(r'^ontology/(?P<onto_pk>\d+)/submission/edit/(?P<pk>\d+)$',
        login_required(views.SubmissionUpdateView.as_view()),
        name='edit_submission'),
]
