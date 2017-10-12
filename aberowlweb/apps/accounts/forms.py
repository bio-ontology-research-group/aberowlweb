from django import forms
from django.utils.translation import ugettext_lazy as _
from accounts.models import UserProfile


class UserProfileForm(forms.ModelForm):

    first_name = forms.CharField(
        label=_('First name'),
        max_length=30,)

    last_name = forms.CharField(
        label=_('Last name'),
        max_length=30,)

    class Meta:
        model = UserProfile
        fields = ['birth_date', 'gender']
