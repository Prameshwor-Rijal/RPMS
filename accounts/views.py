from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from dashboard.decorators import role_required

from .forms import (
    AuthorRegistrationForm,
    ManagedAccountCreationForm,
)
from .models import User


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect(
            "dashboard_redirect",
        )

    if request.method == "POST":
        form = AuthorRegistrationForm(
            request.POST,
        )

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
            )

            return redirect(
                "dashboard_redirect",
            )

    else:
        form = AuthorRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


@role_required([User.Role.JOURNAL_OWNER])
def managed_account_list(request):
    managed_accounts = (
        User.objects.filter(
            created_by=request.user,
            role__in=[
                User.Role.EDITOR,
                User.Role.REVIEWER,
            ],
        )
        .order_by(
            "role",
            "username",
        )
    )

    return render(
        request,
        "accounts/managed_account_list.html",
        {
            "managed_accounts": managed_accounts,
        },
    )


@role_required([User.Role.JOURNAL_OWNER])
def managed_account_create(request):
    if request.method == "POST":
        form = ManagedAccountCreationForm(
            request.POST,
        )

        if form.is_valid():
            user = form.save(
                commit=False,
            )

            user.created_by = request.user

            user.save()

            messages.success(
                request,
                (
                    f"{user.get_role_display()} account "
                    f"'{user.username}' created successfully."
                ),
            )

            return redirect(
                "managed_account_list",
            )

    else:
        form = ManagedAccountCreationForm()

    return render(
        request,
        "accounts/managed_account_form.html",
        {
            "form": form,
        },
    )