from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from aberowl import api_views

urlpatterns = [
    url(r'^searchclasses/$',
        api_views.SearchClassesAPIView.as_view(), name='api-searchclasses'),
    url(r'^querynames/$',
        api_views.QueryNamesAPIView.as_view(), name='api-querynames'),
    url(r'^queryontologies/$',
        api_views.QueryOntologiesAPIView.as_view(), name='api-queryontologies'),
    url(r'^backend/$',
        api_views.BackendAPIView.as_view(), name='api-backend'),
    url(r'^ontologies/$',
        api_views.OntologyListAPIView.as_view(), name='api-ontologies'),
    url(r'^classes/$',
        api_views.ClassInfoAPIView.as_view(), name='api-classinfo'),
    url(r'^mostsimilar/$',
        api_views.MostSimilarAPIView.as_view(), name='api-mostsimilar'),
    url(r'^sparql/$',
        api_views.SparqlAPIView.as_view(), name='api-sparql'),
    url(r'^dlquery/$',
        api_views.DLQueryAPIView.as_view(), name='api-dlquery'),
    url(r'^dlquery/logs$',
        api_views.DLQueryLogsDownloadAPIView.as_view(), name='api-dlquery-logs'),
    url(r'ontology/(?P<acronym>[-\w]+)/objectproperty/$',
        api_views.ListOntologyObjectPropertiesView.as_view(), name='api-ontology_object_properties_list'),
    url(r'^ontology/(?P<acronym>[-\w]+)/objectproperty/(?P<property_iri>.+)$',
        api_views.GetOntologyObjectPropertyView.as_view(), name='api-ontology_object_properties_details'),
    url(r'instance/$',
        api_views.ListInstanceAPIView.as_view(), name='api-instance-list'),
]
