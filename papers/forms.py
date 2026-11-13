from django import forms
from django.core.validators import FileExtensionValidator
from django.utils import timezone

from publications.models import Publication

from .models import Paper


class PaperSubmissionForm(forms.ModelForm):
    paper_file = forms.FileField(
        label="Paper PDF",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    class Meta:
        model = Paper
        fields = (
            "publication",
            "title",
            "abstract",
            "keywords",
            "research_category",
            "paper_file",
        )

        widgets = {
            "abstract": forms.Textarea(attrs={"rows": 6}),
            "keywords": forms.TextInput(
                attrs={"placeholder": "Example: AI, machine learning, healthcare"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.localdate()

        self.fields["publication"].queryset = Publication.objects.filter(
            status=Publication.Status.OPEN,
            submission_open_date__lte=today,
            submission_deadline__gte=today,
        ).order_by("submission_deadline")

class InitialScreeningForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = ("status",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.status == Paper.Status.SUBMITTED:
            self.fields["status"].choices = [
                (
                    Paper.Status.UNDER_INITIAL_REVIEW,
                    "Under Initial Review",
                ),
                (
                    Paper.Status.READY_FOR_REVIEW,
                    "Ready for Reviewer Assignment",
                ),
                (
                    Paper.Status.REJECTED,
                    "Rejected",
                ),
            ]
        else:
            self.fields["status"].choices = [
                (
                    Paper.Status.READY_FOR_REVIEW,
                    "Ready for Reviewer Assignment",
                ),
                (
                    Paper.Status.REJECTED,
                    "Rejected",
                ),
            ]

class FinalDecisionForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = ("status",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = [
            (
                Paper.Status.ACCEPTED,
                "Accepted",
            ),
            (
                Paper.Status.REJECTED,
                "Rejected",
            ),
        ]