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
        "manage/<int:pk>/copyediting/start/",
        views.start_copyediting,
        name="start_copyediting",
    ),

    path(
        "manage/<int:pk>/copyediting/correction/",
        views.request_copyediting_correction,
        name="request_copyediting_correction",
    ),

    path(
        "manage/<int:pk>/copyediting/complete/",
        views.complete_copyediting,
        name="complete_copyediting",
    ),

    path(
        "manage/<int:pk>/",
        views.admin_paper_detail,
        name="admin_paper_detail",
    ),

    path(
        "manage/review-workflow/",
        views.editor_review_workflow,
        name="editor_review_workflow",
    ),

    path(
        "owner/<int:pk>/production/start/",
        views.start_production,
        name="start_production",
    ),

    path(
        "owner/<int:pk>/production/publish/",
        views.publish_paper,
        name="publish_paper",
    ),

    path(
        "owner/<int:pk>/",
        views.journal_owner_paper_detail,
        name="journal_owner_paper_detail",
    ),

    path(
        "version/<int:version_id>/file/",
        views.paper_version_file,
        name="paper_version_file",
    ),

    path(
        "<int:pk>/copyediting/submit/",
        views.copyediting_submission,
        name="copyediting_submission",
    ),

    path(
        "<int:pk>/revision/",
        views.paper_revision_upload,
        name="paper_revision_upload",
    ),
    
    path(
        "<int:pk>/",
        views.paper_detail,
        name="paper_detail",
    ),
]