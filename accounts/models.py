from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        AUTHOR = "AUTHOR", "Author"
        REVIEWER = "REVIEWER", "Reviewer"

    role = models.CharField(
        max_length=10,
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
