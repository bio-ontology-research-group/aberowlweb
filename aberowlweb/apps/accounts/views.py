# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic import DetailView
from django.contrib.auth.models import User


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
        return context
