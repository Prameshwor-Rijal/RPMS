from django.conf import settings
from django.db import models
from django.utils import timezone


class Publication(models.Model):
    class PublicationType(models.TextChoices):
        CONFERENCE = "CONFERENCE", "Conference"
        JOURNAL = "JOURNAL", "Journal"

    # Temporary legacy status.
    # We will remove this after the rest of the project
    # has been migrated to the new workflow.

    class LifecycleStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    class SubmissionStatus(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        OPEN = "OPEN", "Open for Submission"
        CLOSED = "CLOSED", "Closed for Submission"

    name = models.CharField(max_length=255)

    publication_type = models.CharField(
        max_length=20,
        choices=PublicationType.choices,
    )

    description = models.TextField()

    # Journal-specific fields
    issn = models.CharField(
        max_length=20,
        blank=True,
    )

    volume = models.CharField(
        max_length=20,
        blank=True,
    )

    issue = models.CharField(
        max_length=20,
        blank=True,
    )

    publication_frequency = models.CharField(
        max_length=50,
        blank=True,
    )

    # Conference-specific fields
    organizer = models.CharField(
        max_length=255,
        blank=True,
    )

    venue = models.CharField(
        max_length=255,
        blank=True,
    )

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

    # Temporary legacy field.

    lifecycle_status = models.CharField(
        max_length=20,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_publications",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_publications",
        limit_choices_to={"role": "JOURNAL_OWNER"},
    )

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_publications",
        limit_choices_to={"role": "EDITOR"},
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def submission_status(self):
        today = timezone.localdate()

        if self.lifecycle_status != self.LifecycleStatus.ACTIVE:
            return self.SubmissionStatus.CLOSED

        if today < self.submission_open_date:
            return self.SubmissionStatus.UPCOMING

        if today > self.submission_deadline:
            return self.SubmissionStatus.CLOSED

        return self.SubmissionStatus.OPEN

    @property
    def submission_status_display(self):
        return self.SubmissionStatus(
            self.submission_status
        ).label

    def __str__(self):
        return self.name