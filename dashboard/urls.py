from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "dashboard/",
        views.dashboard_redirect,
        name="dashboard_redirect",
    ),
    path(
        "journal-owner-dashboard/",
        views.journal_owner_dashboard,
        name="journal_owner_dashboard",
    ),
    path(
        "editor-dashboard/",
        views.editor_dashboard,
        name="editor_dashboard",
    ),
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
    path(
        "author-dashboard/",
        views.author_dashboard,
        name="author_dashboard",
    ),
    path(
        "reviewer-dashboard/",
        views.reviewer_dashboard,
        name="reviewer_dashboard",
    ),
]