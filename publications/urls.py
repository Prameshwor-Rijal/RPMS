from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.publication_list,
        name="publication_list",
    ),

    path(
        "available/",
        views.available_publications,
        name="available_publications",
    ),

    path(
        "create/",
        views.publication_create,
        name="publication_create",
    ),

    path(
        "editorial-management/",
        views.editorial_management,
        name="editorial_management",
    ),

    path(
        "<int:pk>/edit/",
        views.publication_update,
        name="publication_update",
    ),

    path(
        "<int:pk>/delete/",
        views.publication_delete,
        name="publication_delete",
    ),

    path(
        "<int:pk>/",
        views.publication_detail,
        name="publication_detail",
    ),
]