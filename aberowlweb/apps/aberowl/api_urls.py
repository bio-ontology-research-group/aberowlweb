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
        api_views.DLQueryLogsDownloadAPIView.as_view(), name='api-dlquery-logs')
]
