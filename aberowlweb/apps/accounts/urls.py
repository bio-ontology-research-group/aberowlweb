from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from accounts.views import ProfileDetailView

urlpatterns = [
    url(r'^', include('allauth.account.urls')),
    url(r'^profile/$', login_required(
        ProfileDetailView.as_view()), name='profile'),
]
