# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.models import User
from accounts.forms import UserProfileForm
from accounts.models import UserProfile
from aberowl.models import Ontology


class ProfileDetailView(DetailView):
    model = User
    template_name = 'account/profile/view.html'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            return self.request.user
        return super(ProfileDetailView, self).get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super(ProfileDetailView, self).get_context_data(**kwargs)
        context['ontologies'] = self.get_object().created_ontologies
        return context


class ProfileUpdateView(UpdateView):

    form_class = UserProfileForm
    model = UserProfile
    template_name = 'account/profile/edit.html'

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_success_url(self, *args, **kwargs):
        return reverse('profile')
