from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.reviewer_assignment_list,
        name="reviewer_assignment_list",
    ),

    path(
        "assign/<int:paper_pk>/",
        views.reviewer_assignment_create,
        name="reviewer_assignment_create",
    ),

    path(
        "<int:pk>/",
        views.reviewer_assignment_detail,
        name="reviewer_assignment_detail",
    ),
]