from django import forms
from django.utils import timezone
from django.db.models import Max
from subprocess import Popen, PIPE, DEVNULL
import json
from aberowl.tasks import classify_ontology, reload_ontology, index_submission
from aberowl.models import Ontology, Submission
import shutil
import os
from django.conf import settings

ABEROWL_SERVER_URL = getattr(
    settings, 'ABEROWL_SERVER_URL', 'http://localhost/')

class OntologyForm(forms.ModelForm):

    class Meta:
        model = Ontology
        fields = ('acronym', 'name', 'species', 'topics')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(OntologyForm, self).__init__(*args, **kwargs)
        
    def save(self):
        if not self.instance.pk:
            self.instance = super(OntologyForm, self).save(commit=False)
            self.instance.created_by = self.request.user
        else:
            self.instance.modified_by = self.request.user
            self.instance.date_modified = timezone.now()
        self.instance.save()
        return self.instance
        


class SubmissionForm(forms.ModelForm):

    version = forms.CharField()
    ontology_file = forms.FileField(required=False)
    
    class Meta:
        model = Submission
        fields = (
            'version', 'description', 'publication',
            'documentation', 'home_page', 'has_ontology_language',
            'ontology_file')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.ontology = kwargs.pop('ontology', None)
        super(SubmissionForm, self).__init__(*args, **kwargs)


    def clean_ontology_file(self):
        ontology_file = self.cleaned_data['ontology_file']
        if self.instance.pk is None and ontology_file is None:
            raise ValidationError('Required when creating a submission!')
        if ontology_file is not None:
            filepath = ontology_file.temporary_file_path()
            result = classify_ontology.delay(filepath)
            result = result.get()
            if result['classifiable']:
                self.metrics = result
            else:
                raise forms.ValidationError('Unloadable ontology file')
            
        return ontology_file
    
    def save(self):
        if self.instance.pk is None:
            self.instance = super(SubmissionForm, self).save(commit=False)
            self.instance.ontology = self.ontology
            submission_id = self.ontology.submissions.aggregate(
               Max('submission_id'))['submission_id__max'] or 0
            submission_id += 1
            self.instance.submission_id = submission_id
            self.instance.date_created = timezone.now()
            self.instance.date_released = timezone.now()
        ontology_file = self.cleaned_data['ontology_file']
        if ontology_file is not None:
            shutil.move(
                ontology_file.temporary_file_path(),
                self.instance.get_filepath())
            os.chmod(self.instance.get_filepath(), 0o664)
            shutil.copy(
                self.instance.get_filepath(),
                self.instance.get_filepath('latest'))
            self.instance.nb_inconsistent = self.metrics['incon']
            self.instance.status = self.metrics['status']
            self.instance.classifiable = True
            self.instance.nb_classes = self.metrics['nb_classes']
            self.instance.nb_properties = self.metrics['nb_properties']
            self.instance.nb_individuals = self.metrics['nb_individuals']
            self.instance.max_depth = self.metrics['max_depth']
            self.instance.max_children = self.metrics['max_children']
            self.instance.avg_children = self.metrics['avg_children']
            self.ontology.status = self.metrics['status']
            self.ontology.save()
            ontIRI = ABEROWL_SERVER_URL + self.instance.get_filepath()
            reload_ontology.delay(self.ontology.acronym, ontIRI)
        self.instance.save()
        index_submission.delay(self.ontology.pk, self.instance.pk)
        return self.instance
    
