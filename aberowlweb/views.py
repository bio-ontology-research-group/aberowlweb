from django.views.generic.base import TemplateView
from django.shortcuts import redirect


class HomePageView(TemplateView):

    template_name = 'home.html'


class AboutPageView(TemplateView):

    template_name = 'about.html'

