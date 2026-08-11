from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        JOURNAL_OWNER = "JOURNAL_OWNER", "Journal Owner"
        EDITOR = "EDITOR", "Editor"
        AUTHOR = "AUTHOR", "Author"
        REVIEWER = "REVIEWER", "Reviewer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AUTHOR,
    )

    institution = models.CharField(
        max_length=255,
        blank=True,
    )

    area_of_expertise = models.CharField(
        max_length=255,
        blank=True,
    )

    def __str__(self):
        return self.username
