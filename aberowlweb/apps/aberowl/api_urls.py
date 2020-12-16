from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from aberowl import api_views

urlpatterns = [
    url(r'^class/_startwith$',
        api_views.FindClassByMethodStartWithAPIView.as_view(), name='api-find_class_startwith'),
    url(r'^class/_find$',
        api_views.FindClassAPIView.as_view(), name='api-find_class'),
    url(r'^backend/$',
        api_views.BackendAPIView.as_view(), name='api-backend'),
    url(r'^class/_similar$',
        api_views.MostSimilarAPIView.as_view(), name='api-find_class_similar'),
    url(r'^sparql/$',
        api_views.SparqlAPIView.as_view(), name='api-sparql'),
    url(r'^dlquery$',
        api_views.DLQueryAPIView.as_view(), name='api-dlquery'),
    url(r'^dlquery/logs$',
        api_views.DLQueryLogsDownloadAPIView.as_view(), name='api-dlquery_logs'),
    url(r'^ontology/$',
        api_views.ListOntologyAPIView.as_view(), name='api-list_ontologies'),
    url(r'^ontology/_find$',
        api_views.FindOntologyAPIView.as_view(), name='api-find_ontology'),
    url(r'^ontology/(?P<acronym>[-\w]+)/class/_matchsuperclasses$', 
        api_views.MatchSuperClasses.as_view(), name='api-matach_super_class'),
    url(r'ontology/(?P<acronym>[-\w]+)/objectproperty/$',
        api_views.ListOntologyObjectPropertiesView.as_view(), name='api-ontology_object_properties_list'),
    url(r'^ontology/(?P<acronym>[-\w]+)/objectproperty/(?P<property_iri>.+)$',
        api_views.GetOntologyObjectPropertyView.as_view(), name='api-ontology_object_property_details'),
    url(r'^ontology/(?P<acronym>[-\w]+)/class/(?P<class_iri>.+)$',
        api_views.GetOntologyClassView.as_view(), name='api-ontology_class_details'),
    url(r'^ontology/(?P<acronym>[-\w]+)/root/(?P<class_iri>.+)$',
        api_views.FindOntologyRootClassView.as_view(), name='api-ontology_class_root'),
    url(r'instance/$',
        api_views.ListInstanceAPIView.as_view(), name='api-instance_list'),
]


