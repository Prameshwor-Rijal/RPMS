from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import User
from .decorators import role_required


def home(request):
    return render(request, "home.html")


@login_required
def dashboard_redirect(request):
    if request.user.is_superuser or request.user.role == User.Role.ADMIN:
        return redirect("admin_dashboard")

    if request.user.role == User.Role.REVIEWER:
        return redirect("reviewer_dashboard")

    return redirect("author_dashboard")


@role_required([User.Role.ADMIN])
def admin_dashboard(request):
    return render(request, "dashboard/admin_dashboard.html")


@role_required([User.Role.AUTHOR])
def author_dashboard(request):
    return render(request, "dashboard/author_dashboard.html")


@role_required([User.Role.REVIEWER])
def reviewer_dashboard(request):
    return render(request, "dashboard/reviewer_dashboard.html")
