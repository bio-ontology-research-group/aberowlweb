"""aberowlweb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from aberowlweb.views import HomePageView, AboutPageView
from django.conf import settings
from django.views.generic import TemplateView
from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='AberOwl API')

urlpatterns = [
    # url(r'^$', HomePageView.as_view(), name='home'),
    url(r'^', include('aberowl.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^about/$', AboutPageView.as_view(), name='about'),
    url(r'^healthcheck', TemplateView.as_view(template_name='health.html')),
    url(r'docs/', schema_view),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
