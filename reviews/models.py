from django.conf import settings
from django.db import models

from papers.models import Paper


class ReviewerAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assigned"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"
        COMPLETED = "COMPLETED", "Completed"

    class Recommendation(models.TextChoices):
        ACCEPT = "ACCEPT", "Recommend Accept"
        REJECT = "REJECT", "Recommend Reject"

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
                fields=["paper", "reviewer"],
                name="unique_paper_reviewer_assignment",
            )
        ]

    def __str__(self):
        return (
            f"{self.paper.title} assigned to "
            f"{self.reviewer.username}"
        )