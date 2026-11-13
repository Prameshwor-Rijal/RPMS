from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "accounts/",
        include("accounts.urls"),
    ),

    path(
        "publications/",
        include("publications.urls"),
    ),

    path(
        "papers/",
        include("papers.urls"),
    ),

    path(
        "reviews/",
        include("reviews.urls"),
    ),

    path(
        "",
        include("dashboard.urls"),
    ),
]