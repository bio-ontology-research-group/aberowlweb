from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from aberowl.views import MainView, OntologyListView, OntologyDetailView

urlpatterns = [
    url(r'^$', MainView.as_view(), name='aberowl-main'),
    url(r'^ontology/$', OntologyListView.as_view(), name='ontology-list'),
    url(r'^ontology/(?P<onto>[-\w]+)/$',
        OntologyDetailView.as_view(), name='ontology'),
    url(r'^api/', include('aberowl.api_urls')),
]
