from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from accounts.views import ProfileDetailView, ProfileUpdateView

urlpatterns = [
    url(r'^', include('allauth.account.urls')),
    url(r'^profile/$', login_required(
        ProfileDetailView.as_view()), name='profile'),
    url(r'^profile/edit/$', login_required(
        ProfileUpdateView.as_view()), name='profile_edit'),
]
