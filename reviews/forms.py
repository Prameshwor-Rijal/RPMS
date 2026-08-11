from django import forms

from accounts.models import User

from .models import ReviewerAssignment


class ReviewerAssignmentForm(forms.ModelForm):
    class Meta:
        model = ReviewerAssignment
        fields = ("reviewer",)

    def __init__(
        self,
        *args,
        paper=None,
        review_round=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        reviewers = User.objects.filter(
            role=User.Role.REVIEWER,
            is_active=True,
        )

        if review_round:
            assigned_reviewer_ids = (
                review_round.reviewer_assignments.values_list(
                    "reviewer_id",
                    flat=True,
                )
            )

            reviewers = reviewers.exclude(
                id__in=assigned_reviewer_ids,
            )

        elif paper:
            # Temporary compatibility with the old assignment view.
            assigned_reviewer_ids = (
                paper.reviewer_assignments.values_list(
                    "reviewer_id",
                    flat=True,
                )
            )

            reviewers = reviewers.exclude(
                id__in=assigned_reviewer_ids,
            )

        self.fields["reviewer"].queryset = reviewers.order_by(
            "first_name",
            "username",
        )