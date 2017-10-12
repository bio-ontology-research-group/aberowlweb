from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from aberowl.views import OntologiesListView

urlpatterns = [
    url(r'^ontologies/$', OntologiesListView.as_view(), name='ontologies'),
]
