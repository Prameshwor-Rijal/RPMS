from django import forms

from accounts.models import User

from .models import ReviewerAssignment


class ReviewerAssignmentForm(forms.ModelForm):
    class Meta:
        model = ReviewerAssignment
        fields = (
            "reviewer",
        )

    def __init__(
        self,
        *args,
        paper=None,
        review_round=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        owner = None

        if review_round:
            owner = (
                review_round
                .paper
                .publication
                .owner
            )

        elif paper:
            owner = (
                paper
                .publication
                .owner
            )

        # Reviewers are isolated by Journal Owner.
        # Only Reviewers created by the owner of this
        # paper's publication can be assigned.
        if owner:
            reviewers = User.objects.filter(
                role=User.Role.REVIEWER,
                is_active=True,
                created_by=owner,
            )
        else:
            reviewers = User.objects.none()

        if review_round:
            assigned_reviewer_ids = (
                review_round
                .reviewer_assignments
                .values_list(
                    "reviewer_id",
                    flat=True,
                )
            )

            # Exclude only Reviewers already assigned
            # to the current review round.
            # The same Reviewer can still be assigned
            # again in a later review round.
            reviewers = reviewers.exclude(
                id__in=assigned_reviewer_ids,
            )

        elif paper:
            # Compatibility with the older assignment flow.
            assigned_reviewer_ids = (
                paper
                .reviewer_assignments
                .values_list(
                    "reviewer_id",
                    flat=True,
                )
            )

            reviewers = reviewers.exclude(
                id__in=assigned_reviewer_ids,
            )

        self.fields[
            "reviewer"
        ].queryset = reviewers.order_by(
            "first_name",
            "username",
        )