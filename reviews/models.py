from django.conf import settings
from django.db import models

from papers.models import Paper, PaperVersion

class ReviewRound(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        REVISION_REQUIRED = (
            "REVISION_REQUIRED",
            "Revision Required",
        )
        COMPLETED = "COMPLETED", "Completed"

    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="review_rounds",
    )

    paper_version = models.OneToOneField(
        PaperVersion,
        on_delete=models.PROTECT,
        related_name="review_round",
    )

    round_number = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-round_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["paper", "round_number"],
                name="unique_paper_review_round",
            )
        ]

    def __str__(self):
        return (
            f"{self.paper.title} - "
            f"Review Round {self.round_number}"
        )

class ReviewerAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assigned"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"
        COMPLETED = "COMPLETED", "Completed"

    class Recommendation(models.TextChoices):
        ACCEPT = "ACCEPT", "Recommend Accept"
        REJECT = "REJECT", "Recommend Reject"
        REVISION = "REVISION", "Request Revision"

    review_round = models.ForeignKey(
        ReviewRound,
        on_delete=models.CASCADE,
        related_name="reviewer_assignments",
    )

    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="reviewer_assignments",
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="review_assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_reviews",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
    )

    recommendation = models.CharField(
        max_length=10,
        choices=Recommendation.choices,
        blank=True,
        default="",
    )

    comments = models.TextField(
        blank=True,
        default="",
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    responded_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-assigned_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["review_round", "reviewer"],
                name="unique_review_round_reviewer_assignment",
            )
        ]

    def __str__(self):
        return (
            f"{self.paper.title} assigned to "
            f"{self.reviewer.username}"
        )