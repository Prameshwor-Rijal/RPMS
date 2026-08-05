from functools import wraps

from django.shortcuts import redirect


def role_required(allowed_roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            if request.user.role not in allowed_roles:
                return redirect("dashboard_redirect")

            return view_function(request, *args, **kwargs)

        return wrapper

    return decorator
