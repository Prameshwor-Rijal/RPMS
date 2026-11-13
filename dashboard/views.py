from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import User
from papers.models import Paper

from .decorators import role_required


def home(request):
    return render(
        request,
        "home.html",
    )


@login_required
def dashboard_redirect(request):
    # Technical System Admin uses Django Admin,
    # not any RPMS business-role dashboard.
    if request.user.is_superuser:
        return redirect(
            "/admin/",
        )

    if request.user.role == User.Role.JOURNAL_OWNER:
        return redirect(
            "journal_owner_dashboard",
        )

    if request.user.role == User.Role.EDITOR:
        return redirect(
            "editor_dashboard",
        )

    if request.user.role == User.Role.REVIEWER:
        return redirect(
            "reviewer_dashboard",
        )

    if request.user.role == User.Role.AUTHOR:
        return redirect(
            "author_dashboard",
        )

    return redirect(
        "home",
    )


@role_required([User.Role.JOURNAL_OWNER])
def journal_owner_dashboard(request):
    monitored_papers = (
        Paper.objects.filter(
            publication__owner=request.user,
        )
        .select_related(
            "publication",
            "corresponding_author",
        )
        .order_by(
            "-submitted_at",
        )
    )

    return render(
        request,
        "dashboard/journal_owner_dashboard.html",
        {
            "monitored_papers": monitored_papers,
        },
    )


@role_required([User.Role.EDITOR])
def editor_dashboard(request):
    assigned_publications = (
        request.user
        .assigned_publications
        .all()
        .order_by(
            "name",
        )
    )

    return render(
        request,
        "dashboard/editor_dashboard.html",
        {
            "assigned_publications": assigned_publications,
        },
    )


@role_required([User.Role.AUTHOR])
def author_dashboard(request):
    return render(
        request,
        "dashboard/author_dashboard.html",
    )


@role_required([User.Role.REVIEWER])
def reviewer_dashboard(request):
    return render(
        request,
        "dashboard/reviewer_dashboard.html",
    )