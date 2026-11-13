from django.urls import path

from . import views


urlpatterns = [
    path("submit/", views.paper_submit, name="paper_submit"),

    path(
        "my-submissions/",
        views.my_submissions,
        name="my_submissions",
    ),

    path(
        "manage/",
        views.admin_paper_list,
        name="admin_paper_list",
    ),

    path(
        "manage/<int:pk>/screening/",
        views.paper_initial_screening,
        name="paper_initial_screening",
    ),

    path(
        "manage/<int:pk>/decision/",
        views.paper_final_decision,
        name="paper_final_decision",
    ),

    path(
        "manage/<int:pk>/",
        views.admin_paper_detail,
        name="admin_paper_detail",
    ),

    path(
        "<int:pk>/",
        views.paper_detail,
        name="paper_detail",
    ),
]