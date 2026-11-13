from django import forms
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


class ManagedAccountCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (
                User.Role.EDITOR,
                "Editor",
            ),
            (
                User.Role.REVIEWER,
                "Reviewer",
            ),
        ],
        label="Account Role",
    )

    email = forms.EmailField(
        required=True,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "institution",
            "area_of_expertise",
            "role",
            "password1",
            "password2",
        )

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get("role")

        area_of_expertise = cleaned_data.get(
            "area_of_expertise",
            "",
        ).strip()

        if (
            role == User.Role.REVIEWER
            and not area_of_expertise
        ):
            self.add_error(
                "area_of_expertise",
                (
                    "Area of expertise is required "
                    "for Reviewer accounts."
                ),
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = self.cleaned_data["role"]

        if commit:
            user.save()

        return user