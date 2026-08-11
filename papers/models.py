from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from publications.models import Publication


def paper_file_path(instance, filename):
    return (
        f"papers/{instance.paper_id}/"
        f"version_{instance.version_number}/{filename}"
    )


class Paper(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"

        UNDER_INITIAL_REVIEW = (
            "UNDER_INITIAL_REVIEW",
            "Under Initial Review",
        )

        READY_FOR_REVIEW = (
            "READY_FOR_REVIEW",
            "Ready for Reviewer Assignment",
        )

        UNDER_REVIEW = (
            "UNDER_REVIEW",
            "Under Review",
        )

        REVIEW_COMPLETED = (
            "REVIEW_COMPLETED",
            "Review Completed",
        )

        REVISION_REQUIRED = (
            "REVISION_REQUIRED",
            "Revision Required",
        )

        ACCEPTED = (
            "ACCEPTED",
            "Accepted",
        )

        REJECTED = (
            "REJECTED",
            "Rejected",
        )

        COPYEDITING = (
            "COPYEDITING",
            "Copyediting",
        )

        COPYEDITING_CORRECTION_REQUIRED = (
            "COPYEDITING_CORRECTION_REQUIRED",
            "Copyediting Correction Required",
        )

        READY_FOR_PRODUCTION = (
            "READY_FOR_PRODUCTION",
            "Ready for Production",
        )

        IN_PRODUCTION = (
            "IN_PRODUCTION",
            "In Production",
        )

        PUBLISHED = (
            "PUBLISHED",
            "Published",
        )

    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="papers",
    )

    corresponding_author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_papers",
    )

    title = models.CharField(
        max_length=255,
    )

    abstract = models.TextField()

    keywords = models.CharField(
        max_length=500,
    )

    research_category = models.CharField(
        max_length=255,
    )

    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_review_overdue(self):
        review_deadline = self.publication.review_deadline

        if not review_deadline:
            return False

        review_statuses = {
            self.Status.READY_FOR_REVIEW,
            self.Status.UNDER_REVIEW,
            self.Status.REVISION_REQUIRED,
        }

        if self.status not in review_statuses:
            return False

        if hasattr(review_deadline, "date"):
            review_deadline = review_deadline.date()

        return timezone.localdate() > review_deadline


class PaperVersion(models.Model):
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version_number = models.PositiveIntegerField(
        default=1,
    )

    file = models.FileField(
        upload_to=paper_file_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ],
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_paper_versions",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-version_number"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "paper",
                    "version_number",
                ],
                name="unique_paper_version_number",
            )
        ]

    def __str__(self):
        return (
            f"{self.paper.title} "
            f"- Version {self.version_number}"
        )


class FinalDecision(models.Model):
    class Decision(models.TextChoices):
        ACCEPTED = (
            "ACCEPTED",
            "Accepted",
        )

        REJECTED = (
            "REJECTED",
            "Rejected",
        )

    paper = models.OneToOneField(
        Paper,
        on_delete=models.CASCADE,
        related_name="final_decision",
    )

    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
    )

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="final_decisions_made",
    )

    note = models.TextField(
        blank=True,
        default="",
    )

    decided_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.paper.title} - "
            f"{self.get_decision_display()}"
        )

class Copyediting(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = (
            "IN_PROGRESS",
            "In Progress",
        )

        CORRECTION_REQUIRED = (
            "CORRECTION_REQUIRED",
            "Correction Required",
        )

        CORRECTION_SUBMITTED = (
            "CORRECTION_SUBMITTED",
            "Correction Submitted",
        )

        COMPLETED = (
            "COMPLETED",
            "Completed",
        )

    paper = models.OneToOneField(
        Paper,
        on_delete=models.CASCADE,
        related_name="copyediting",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="copyediting_started",
    )

    correction_note = models.TextField(
        blank=True,
        default="",
    )

    author_note = models.TextField(
        blank=True,
        default="",
    )

    corrected_version = models.OneToOneField(
        PaperVersion,
        on_delete=models.PROTECT,
        related_name="copyediting_submission",
        blank=True,
        null=True,
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    correction_requested_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    correction_submitted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="copyediting_completed",
        blank=True,
        null=True,
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return (
            f"{self.paper.title} - "
            f"{self.get_status_display()}"
        )

class Production(models.Model):
    class Status(models.TextChoices):
        IN_PRODUCTION = (
            "IN_PRODUCTION",
            "In Production",
        )

        PUBLISHED = (
            "PUBLISHED",
            "Published",
        )

    paper = models.OneToOneField(
        Paper,
        on_delete=models.CASCADE,
        related_name="production",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PRODUCTION,
    )

    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="productions_started",
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    production_note = models.TextField(
        blank=True,
        default="",
    )

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="papers_published",
        blank=True,
        null=True,
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return (
            f"{self.paper.title} - "
            f"{self.get_status_display()}"
        )