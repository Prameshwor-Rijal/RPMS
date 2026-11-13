from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from publications.models import Publication


def paper_file_path(instance, filename):
    return (
        f"papers/{instance.paper_id}/" f"version_{instance.version_number}/{filename}"
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
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"

        REVIEW_COMPLETED = (
            "REVIEW_COMPLETED",
            "Review Completed",
        )
        REVISION_REQUIRED = (
            "REVISION_REQUIRED",
            "Revision Required",
        )
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

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

    title = models.CharField(max_length=255)
    abstract = models.TextField()
    keywords = models.CharField(max_length=500)
    research_category = models.CharField(max_length=255)

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PaperVersion(models.Model):
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version_number = models.PositiveIntegerField(default=1)

    file = models.FileField(
        upload_to=paper_file_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_paper_versions",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["paper", "version_number"],
                name="unique_paper_version_number",
            )
        ]

    def __str__(self):
        return f"{self.paper.title} " f"- Version {self.version_number}"
