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
]
