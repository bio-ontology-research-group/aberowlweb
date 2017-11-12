from django.views.generic import CreateView, UpdateView, ListView
from django.urls import reverse
from aberowl.models import Ontology, Submission
from aberowl.forms import OntologyForm, SubmissionForm
from aberowlweb.mixins import FormRequestMixin
from django.shortcuts import get_object_or_404

class MyOntologyListView(ListView):

    model = Ontology
    template_name = 'aberowl/manage/list_ontology.html'

    def get_queryset(self, *args, **kwargs):
        return self.request.user.created_ontologies.all().order_by(
            'acronym')
    
    
class OntologyCreateView(FormRequestMixin, CreateView):

    model = Ontology
    form_class = OntologyForm
    template_name = 'aberowl/manage/edit_ontology.html'

    def get_success_url(self):
        kwargs = {'onto_pk': self.object.pk}
        return reverse('create_submission', kwargs=kwargs)


class OntologyUpdateView(FormRequestMixin, UpdateView):

    model = Ontology
    form_class = OntologyForm
    template_name = 'aberowl/manage/edit_ontology.html'

    def get_success_url(self):
        return reverse('list_ontology')

    
class OntologyMixin(object):

    def get_ontology(self):
        if hasattr(self, 'ontology'):
            return self.ontology
        ontology_id = self.kwargs.get('onto_pk', None)
        if ontology_id:
            self.ontology = get_object_or_404(Ontology, pk=ontology_id)
            return self.ontology

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(OntologyMixin, self).get_form_kwargs(*args, **kwargs)
        kwargs['ontology'] = self.get_ontology()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(OntologyMixin, self).get_context_data(*args, **kwargs)
        context['ontology'] = self.get_ontology()
        return context



class SubmissionCreateView(FormRequestMixin, OntologyMixin, CreateView):

    model = Submission
    form_class = SubmissionForm
    template_name = 'aberowl/manage/edit_submission.html'

    def get_success_url(self):
        return reverse('list_ontology')

class SubmissionUpdateView(FormRequestMixin, OntologyMixin, UpdateView):

    model = Submission
    form_class = SubmissionForm
    template_name = 'aberowl/manage/edit_submission.html'

    def get_success_url(self):
        return reverse('list_ontology')
