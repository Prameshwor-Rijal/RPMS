from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Publication


User = get_user_model()


class PublicationManagementTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.admin_user = User.objects.create_user(
            username="publicationadmin",
            password="StrongPass123!",
            role=User.Role.ADMIN,
        )

        self.author_user = User.objects.create_user(
            username="publicationauthor",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

        self.reviewer_user = User.objects.create_user(
            username="publicationreviewer",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
        )

        self.publication = Publication.objects.create(
            name="Test Computing Conference",
            publication_type=Publication.PublicationType.CONFERENCE,
            description="A test research conference.",
            submission_open_date=self.today - timedelta(days=5),
            submission_deadline=self.today + timedelta(days=10),
            review_deadline=self.today + timedelta(days=20),
            event_date=self.today + timedelta(days=30),
            location="Kathmandu",
            status=Publication.Status.OPEN,
            created_by=self.admin_user,
        )

    def publication_data(self, name="New Research Journal"):
        return {
            "name": name,
            "publication_type": Publication.PublicationType.JOURNAL,
            "description": "A journal created during an automated test.",
            "submission_open_date": (
                self.today + timedelta(days=1)
            ).isoformat(),
            "submission_deadline": (
                self.today + timedelta(days=10)
            ).isoformat(),
            "review_deadline": (
                self.today + timedelta(days=20)
            ).isoformat(),
            "event_date": (
                self.today + timedelta(days=30)
            ).isoformat(),
            "location": "Online",
            "status": Publication.Status.DRAFT,
        }

    def test_admin_can_view_publication_list(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("publication_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "publications/publication_list.html",
        )
        self.assertContains(response, self.publication.name)

    def test_author_cannot_view_admin_publication_list(self):
        self.client.force_login(self.author_user)

        response = self.client.get(reverse("publication_list"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_redirect"))

    def test_admin_can_create_publication(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("publication_create"),
            self.publication_data(),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("publication_list"))

        publication = Publication.objects.get(
            name="New Research Journal"
        )

        self.assertEqual(publication.created_by, self.admin_user)
        self.assertEqual(
            publication.publication_type,
            Publication.PublicationType.JOURNAL,
        )

    def test_invalid_dates_do_not_create_publication(self):
        self.client.force_login(self.admin_user)

        data = self.publication_data(name="Invalid Publication")
        data["submission_open_date"] = (
            self.today + timedelta(days=10)
        ).isoformat()
        data["submission_deadline"] = (
            self.today + timedelta(days=5)
        ).isoformat()

        response = self.client.post(
            reverse("publication_create"),
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Publication.objects.filter(
                name="Invalid Publication"
            ).exists()
        )
        self.assertContains(
            response,
            "Submission deadline must be after the opening date.",
        )

    def test_admin_can_view_publication_detail(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "publication_detail",
                kwargs={"pk": self.publication.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "publications/publication_detail.html",
        )
        self.assertContains(response, self.publication.name)

    def test_admin_can_update_publication(self):
        self.client.force_login(self.admin_user)

        updated_data = self.publication_data(
            name="Updated Research Journal"
        )

        response = self.client.post(
            reverse(
                "publication_update",
                kwargs={"pk": self.publication.pk},
            ),
            updated_data,
        )

        self.assertEqual(response.status_code, 302)

        self.publication.refresh_from_db()

        self.assertEqual(
            self.publication.name,
            "Updated Research Journal",
        )
        self.assertEqual(
            response.url,
            reverse(
                "publication_detail",
                kwargs={"pk": self.publication.pk},
            ),
        )

    def test_admin_can_delete_publication(self):
        self.client.force_login(self.admin_user)

        publication_id = self.publication.pk

        response = self.client.post(
            reverse(
                "publication_delete",
                kwargs={"pk": publication_id},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("publication_list"))
        self.assertFalse(
            Publication.objects.filter(pk=publication_id).exists()
        )


class AvailablePublicationTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.admin_user = User.objects.create_user(
            username="availableadmin",
            password="StrongPass123!",
            role=User.Role.ADMIN,
        )

        self.author_user = User.objects.create_user(
            username="availableauthor",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

        self.reviewer_user = User.objects.create_user(
            username="availablereviewer",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
        )

        self.available_publication = self.create_publication(
            name="Available Conference",
            status=Publication.Status.OPEN,
            open_date=self.today - timedelta(days=2),
            deadline=self.today + timedelta(days=10),
        )

        self.closed_publication = self.create_publication(
            name="Closed Conference",
            status=Publication.Status.CLOSED,
            open_date=self.today - timedelta(days=2),
            deadline=self.today + timedelta(days=10),
        )

        self.future_publication = self.create_publication(
            name="Future Conference",
            status=Publication.Status.OPEN,
            open_date=self.today + timedelta(days=5),
            deadline=self.today + timedelta(days=15),
        )

        self.expired_publication = self.create_publication(
            name="Expired Conference",
            status=Publication.Status.OPEN,
            open_date=self.today - timedelta(days=20),
            deadline=self.today - timedelta(days=1),
        )

    def create_publication(
        self,
        name,
        status,
        open_date,
        deadline,
    ):
        return Publication.objects.create(
            name=name,
            publication_type=Publication.PublicationType.CONFERENCE,
            description="Publication filtering test.",
            submission_open_date=open_date,
            submission_deadline=deadline,
            review_deadline=deadline + timedelta(days=10),
            event_date=deadline + timedelta(days=20),
            location="Online",
            status=status,
            created_by=self.admin_user,
        )

    def test_author_sees_only_currently_available_publications(self):
        self.client.force_login(self.author_user)

        response = self.client.get(
            reverse("available_publications")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "publications/available_publications.html",
        )

        publications = response.context["publications"]

        self.assertIn(
            self.available_publication,
            publications,
        )
        self.assertNotIn(
            self.closed_publication,
            publications,
        )
        self.assertNotIn(
            self.future_publication,
            publications,
        )
        self.assertNotIn(
            self.expired_publication,
            publications,
        )

    def test_reviewer_cannot_view_available_publications(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.get(
            reverse("available_publications")
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_redirect"))