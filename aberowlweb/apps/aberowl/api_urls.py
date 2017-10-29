from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from aberowl import api_views

urlpatterns = [
    url(r'^querynames/$',
        api_views.QueryNamesAPIView.as_view(), name='api-querynames'),
    url(r'^queryontologies/$',
        api_views.QueryOntologiesAPIView.as_view(), name='api-queryontologies'),
    url(r'^backend/$',
        api_views.BackendAPIView.as_view(), name='api-backend'),
]
