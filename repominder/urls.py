from django.conf.urls import include, url
from django.contrib import admin

from .apps.core import views

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url("", include("social_django.urls", namespace="social")),
    url(r"^account/$", views.account, name="account"),
    url(r"^watch/(?P<id>\d+)/$", views.repo_details, name="repo"),
    url(
        r"^badge/(?P<selector>.+)/$",
        views.badge_info,
        name="badge_info",
    ),
    url(
        r"^hook/$",
        views.receive_hook,
        name="receive_hook",
    ),
    url(r"^privacy/$", views.PrivacyView.as_view(), name="privacy"),
    url(r"^logout/$", views.logout, name="logout"),
    url(r"^$", views.LoggedOutView.as_view(), name="landing"),
]
