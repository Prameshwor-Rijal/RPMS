from django.contrib.auth.forms import UserCreationForm
from .models import User


class AuthorRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "institution",
            "area_of_expertise",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.AUTHOR

        if commit:
            user.save()

        return user
