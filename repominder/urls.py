from django.contrib import admin
from django.urls import include, re_path

from .apps.core import views

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path("", include("social_django.urls", namespace="social")),
    re_path(r"^account/$", views.account, name="account"),
    re_path(r"^watch/(?P<id>\d+)/$", views.repo_details, name="repo"),
    re_path(
        r"^badge/(?P<selector>.+)/$",
        views.badge_info,
        name="badge_info",
    ),
    re_path(
        r"^hook/$",
        views.receive_hook,
        name="receive_hook",
    ),
    re_path(r"^privacy/$", views.PrivacyView.as_view(), name="privacy"),
    re_path(r"^logout/$", views.logout, name="logout"),
    re_path(r"^$", views.LoggedOutView.as_view(), name="landing"),
]
