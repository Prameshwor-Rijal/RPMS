from django import forms

from .models import Publication


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = (
            "name",
            "publication_type",
            "description",
            "submission_open_date",
            "submission_deadline",
            "review_deadline",
            "event_date",
            "location",
            "status",
        )

        widgets = {
            "submission_open_date": forms.DateInput(attrs={"type": "date"}),
            "submission_deadline": forms.DateInput(attrs={"type": "date"}),
            "review_deadline": forms.DateInput(attrs={"type": "date"}),
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def clean(self):
        cleaned_data = super().clean()

        open_date = cleaned_data.get("submission_open_date")
        submission_deadline = cleaned_data.get("submission_deadline")
        review_deadline = cleaned_data.get("review_deadline")
        event_date = cleaned_data.get("event_date")

        if open_date and submission_deadline and submission_deadline < open_date:
            self.add_error(
                "submission_deadline",
                "Submission deadline must be after the opening date.",
            )

        if (
            submission_deadline
            and review_deadline
            and review_deadline < submission_deadline
        ):
            self.add_error(
                "review_deadline",
                "Review deadline must be after the submission deadline.",
            )

        if review_deadline and event_date and event_date < review_deadline:
            self.add_error(
                "event_date",
                "Event or publication date must be after the review deadline.",
            )

        return cleaned_data
