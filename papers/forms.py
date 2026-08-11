from django import forms
from django.core.validators import FileExtensionValidator
from django.utils import timezone

from publications.models import Publication

from .models import Paper


def validate_pdf_size(file):
    max_size = 10 * 1024 * 1024  # 10 MB

    if file.size > max_size:
        raise forms.ValidationError(
            "PDF file size must not exceed 10 MB."
        )

    return file


def validate_pdf_content(file):
    file.seek(0)
    signature = file.read(5)
    file.seek(0)

    if signature != b"%PDF-":
        raise forms.ValidationError(
            "The uploaded file is not a valid PDF."
        )

    return file


class PaperSubmissionForm(forms.ModelForm):
    paper_file = forms.FileField(
        label="Paper PDF",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"],
            )
        ],
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
            "abstract": forms.Textarea(
                attrs={
                    "rows": 6,
                }
            ),
            "keywords": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Example: AI, machine learning, healthcare"
                    )
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.localdate()

        self.fields["publication"].queryset = (
            Publication.objects.filter(
                lifecycle_status=(
                    Publication.LifecycleStatus.ACTIVE
                ),
                submission_open_date__lte=today,
                submission_deadline__gte=today,
            ).order_by(
                "submission_deadline"
            )
        )

    def clean_paper_file(self):
        paper_file = self.cleaned_data["paper_file"]

        validate_pdf_size(paper_file)
        validate_pdf_content(paper_file)

        return paper_file


class PaperRevisionForm(forms.Form):
    paper_file = forms.FileField(
        label="Revised Paper PDF",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"],
            )
        ],
    )

    def clean_paper_file(self):
        paper_file = self.cleaned_data["paper_file"]

        validate_pdf_size(paper_file)
        validate_pdf_content(paper_file)

        return paper_file


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
    note = forms.CharField(
        label="Decision Note",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": (
                    "Add a note explaining the final decision..."
                ),
            }
        ),
    )

    class Meta:
        model = Paper
        fields = ("status",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].label = "Final Decision"

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


class CopyeditingCorrectionForm(forms.Form):
    correction_note = forms.CharField(
        label="Correction Request",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": (
                    "Describe the formatting, language, citation, "
                    "or other copyediting corrections required..."
                ),
            }
        ),
    )


class CopyeditingSubmissionForm(forms.Form):
    paper_file = forms.FileField(
        label="Corrected Paper (PDF)",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"],
            )
        ],
    )

    author_note = forms.CharField(
        label="Author Note",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": (
                    "Briefly describe the copyediting "
                    "corrections you made..."
                ),
            }
        ),
    )

    def clean_paper_file(self):
        paper_file = self.cleaned_data["paper_file"]

        validate_pdf_size(paper_file)
        validate_pdf_content(paper_file)

        return paper_file