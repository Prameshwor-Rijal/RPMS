from django.conf import settings
from django.db import models


class Publication(models.Model):
    class PublicationType(models.TextChoices):
        CONFERENCE = "CONFERENCE", "Conference"
        JOURNAL = "JOURNAL", "Journal"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open for Submission"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        COMPLETED = "COMPLETED", "Completed"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=255)

    publication_type = models.CharField(
        max_length=20,
        choices=PublicationType.choices,
    )

    description = models.TextField()

    submission_open_date = models.DateField()
    submission_deadline = models.DateField()
    review_deadline = models.DateField()

    event_date = models.DateField(
        blank=True,
        null=True,
    )

    location = models.CharField(
        max_length=255,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_publications",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
