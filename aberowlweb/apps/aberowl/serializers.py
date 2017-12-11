from rest_framework import serializers
from aberowl.models import Ontology, Submission



class SubmissionSerializer(serializers.ModelSerializer):

    download_url = serializers.CharField(source='get_filepath')

    class Meta:
        model = Submission
        exclude = ['ontology', ]
    

class OntologySerializer(serializers.ModelSerializer):

    submission = SubmissionSerializer(
        source='get_latest_submission', read_only=True)

    class Meta:
        model = Ontology
        fields = [
            'acronym', 'name', 'status', 'topics', 'species', 'submission']

