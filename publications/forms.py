from django import forms
from django.utils import timezone

from accounts.models import User

from .models import Publication


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication

        fields = (
            "name",
            "publication_type",
            "description",

            # Journal-specific
            "issn",
            "volume",
            "issue",
            "publication_frequency",

            # Conference-specific
            "organizer",

            # Shared dates
            "submission_open_date",
            "submission_deadline",
            "review_deadline",

            # Conference-specific after review deadline
            "event_date",
            "venue",
            "location",

            # Shared management
            "editors",
            "lifecycle_status",
        )

        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 5}
            ),
            "submission_open_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "submission_deadline": forms.DateInput(
                attrs={"type": "date"}
            ),
            "review_deadline": forms.DateInput(
                attrs={"type": "date"}
            ),
            "event_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "editors": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        owner = kwargs.pop(
            "owner",
            None,
        )

        super().__init__(*args, **kwargs)

        # When editing an existing publication, use its owner
        # if the owner was not explicitly passed to the form.
        if (
            owner is None
            and self.instance.pk
        ):
            owner = self.instance.owner

        # Journal Owners can only assign Editors that belong
        # to their own managed account environment.
        if owner:
            self.fields["editors"].queryset = (
                User.objects.filter(
                    role=User.Role.EDITOR,
                    is_active=True,
                    created_by=owner,
                )
                .order_by("username")
            )
        else:
            self.fields[
                "editors"
            ].queryset = User.objects.none()

        if not self.instance.pk:
            self.fields[
                "submission_open_date"
            ].widget.attrs["min"] = (
                timezone.localdate().isoformat()
            )

    def clean(self):
        cleaned_data = super().clean()

        publication_type = cleaned_data.get(
            "publication_type"
        )

        open_date = cleaned_data.get(
            "submission_open_date"
        )

        submission_deadline = cleaned_data.get(
            "submission_deadline"
        )

        review_deadline = cleaned_data.get(
            "review_deadline"
        )

        event_date = cleaned_data.get(
            "event_date"
        )

        # Journal-specific validation
        if (
            publication_type
            == Publication.PublicationType.JOURNAL
        ):
            if not cleaned_data.get("issn"):
                self.add_error(
                    "issn",
                    "ISSN is required for a journal.",
                )

        # Conference-specific validation
        if (
            publication_type
            == Publication.PublicationType.CONFERENCE
        ):
            if not cleaned_data.get("organizer"):
                self.add_error(
                    "organizer",
                    "Organizer is required for a conference.",
                )

            if not event_date:
                self.add_error(
                    "event_date",
                    "Conference date is required.",
                )

        # Date validation
        if (
            not self.instance.pk
            and open_date
            and open_date < timezone.localdate()
        ):
            self.add_error(
                "submission_open_date",
                (
                    "Submission opening date cannot "
                    "be in the past."
                ),
            )

        if (
            open_date
            and submission_deadline
            and submission_deadline <= open_date
        ):
            self.add_error(
                "submission_deadline",
                (
                    "Submission deadline must be "
                    "after the opening date."
                ),
            )

        if (
            submission_deadline
            and review_deadline
            and review_deadline <= submission_deadline
        ):
            self.add_error(
                "review_deadline",
                (
                    "Review deadline must be after "
                    "the submission deadline."
                ),
            )

        if (
            publication_type
            == Publication.PublicationType.CONFERENCE
            and review_deadline
            and event_date
            and event_date <= review_deadline
        ):
            self.add_error(
                "event_date",
                (
                    "Conference date must be after "
                    "the review deadline."
                ),
            )

        return cleaned_data