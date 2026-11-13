from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    UserLoginView,
    managed_account_create,
    managed_account_list,
    register,
)


urlpatterns = [
    path(
        "login/",
        UserLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "register/",
        register,
        name="register",
    ),
    path(
        "managed-accounts/",
        managed_account_list,
        name="managed_account_list",
    ),
    path(
        "managed-accounts/create/",
        managed_account_create,
        name="managed_account_create",
    ),
]