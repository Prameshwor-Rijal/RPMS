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

        self.owner_user = User.objects.create_user(
            username="publicationowner",
            password="StrongPass123!",
            role=User.Role.JOURNAL_OWNER,
        )

        self.second_owner = User.objects.create_user(
            username="secondowner",
            password="StrongPass123!",
            role=User.Role.JOURNAL_OWNER,
        )

        self.editor_user = User.objects.create_user(
            username="publicationeditor",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            created_by=self.owner_user,
        )

        self.second_editor = User.objects.create_user(
            username="secondeditor",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            created_by=self.second_owner,
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
            created_by=self.owner_user,
        )

        self.publication = Publication.objects.create(
            name="Test Computing Conference",
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description=(
                "A test research conference."
            ),
            organizer="RPMS Research Group",
            venue="Kathmandu",
            submission_open_date=(
                self.today - timedelta(days=5)
            ),
            submission_deadline=(
                self.today + timedelta(days=10)
            ),
            review_deadline=(
                self.today + timedelta(days=20)
            ),
            event_date=(
                self.today + timedelta(days=30)
            ),
            location="Kathmandu",
            lifecycle_status=(
                Publication.LifecycleStatus.ACTIVE
            ),
            created_by=self.owner_user,
            owner=self.owner_user,
        )

        self.publication.editors.add(
            self.editor_user,
        )

        self.second_publication = Publication.objects.create(
            name="Second Owner Conference",
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description=(
                "Publication belonging to another owner."
            ),
            organizer="Second Research Group",
            venue="Pokhara",
            submission_open_date=(
                self.today - timedelta(days=3)
            ),
            submission_deadline=(
                self.today + timedelta(days=12)
            ),
            review_deadline=(
                self.today + timedelta(days=22)
            ),
            event_date=(
                self.today + timedelta(days=32)
            ),
            location="Pokhara",
            lifecycle_status=(
                Publication.LifecycleStatus.ACTIVE
            ),
            created_by=self.second_owner,
            owner=self.second_owner,
        )

        self.second_publication.editors.add(
            self.second_editor,
        )

    def publication_data(
        self,
        name="New Research Conference",
    ):
        return {
            "name": name,
            "publication_type": (
                Publication.PublicationType.CONFERENCE
            ),
            "description": (
                "A conference created during "
                "an automated test."
            ),
            "organizer": "RPMS Test Organization",
            "venue": "Kathmandu Convention Center",
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
            "location": "Kathmandu",
            "lifecycle_status": (
                Publication.LifecycleStatus.DRAFT
            ),
            "editors": [
                self.editor_user.pk,
            ],
        }

    def test_owner_can_view_own_publication_list(self):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse("publication_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "publications/publication_list.html",
        )

        self.assertContains(
            response,
            self.publication.name,
        )

        self.assertNotContains(
            response,
            self.second_publication.name,
        )

    def test_author_cannot_view_publication_management_list(
        self,
    ):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("publication_list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_reviewer_cannot_view_publication_management_list(
        self,
    ):
        self.client.force_login(
            self.reviewer_user,
        )

        response = self.client.get(
            reverse("publication_list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_owner_can_create_publication(self):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.post(
            reverse("publication_create"),
            self.publication_data(),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("publication_list"),
        )

        publication = Publication.objects.get(
            name="New Research Conference",
        )

        self.assertEqual(
            publication.created_by,
            self.owner_user,
        )

        self.assertEqual(
            publication.owner,
            self.owner_user,
        )

        self.assertEqual(
            publication.publication_type,
            Publication.PublicationType.CONFERENCE,
        )

        self.assertEqual(
            publication.lifecycle_status,
            Publication.LifecycleStatus.DRAFT,
        )

        self.assertTrue(
            publication.editors.filter(
                pk=self.editor_user.pk,
            ).exists()
        )

    def test_owner_cannot_assign_another_owners_editor(
        self,
    ):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse("publication_create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        form = response.context["form"]

        editor_queryset = (
            form.fields["editors"].queryset
        )

        self.assertIn(
            self.editor_user,
            editor_queryset,
        )

        self.assertNotIn(
            self.second_editor,
            editor_queryset,
        )

    def test_invalid_dates_do_not_create_publication(self):
        self.client.force_login(
            self.owner_user,
        )

        data = self.publication_data(
            name="Invalid Publication",
        )

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

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Publication.objects.filter(
                name="Invalid Publication",
            ).exists()
        )

        self.assertContains(
            response,
            (
                "Submission deadline must be "
                "after the opening date."
            ),
        )

    def test_owner_can_view_own_publication_detail(self):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse(
                "publication_detail",
                kwargs={
                    "pk": self.publication.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "publications/publication_detail.html",
        )

        self.assertContains(
            response,
            self.publication.name,
        )

    def test_owner_cannot_view_another_owners_publication(
        self,
    ):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse(
                "publication_detail",
                kwargs={
                    "pk": self.second_publication.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_owner_can_update_own_publication(self):
        self.client.force_login(
            self.owner_user,
        )

        updated_data = self.publication_data(
            name="Updated Computing Conference",
        )

        updated_data["lifecycle_status"] = (
            Publication.LifecycleStatus.ACTIVE
        )

        response = self.client.post(
            reverse(
                "publication_update",
                kwargs={
                    "pk": self.publication.pk,
                },
            ),
            updated_data,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.publication.refresh_from_db()

        self.assertEqual(
            self.publication.name,
            "Updated Computing Conference",
        )

        self.assertEqual(
            self.publication.lifecycle_status,
            Publication.LifecycleStatus.ACTIVE,
        )

        self.assertEqual(
            self.publication.owner,
            self.owner_user,
        )

        self.assertEqual(
            response.url,
            reverse(
                "publication_detail",
                kwargs={
                    "pk": self.publication.pk,
                },
            ),
        )

    def test_owner_cannot_update_another_owners_publication(
        self,
    ):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.post(
            reverse(
                "publication_update",
                kwargs={
                    "pk": self.second_publication.pk,
                },
            ),
            self.publication_data(
                name="Unauthorized Update",
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.second_publication.refresh_from_db()

        self.assertEqual(
            self.second_publication.name,
            "Second Owner Conference",
        )

    def test_owner_can_delete_own_publication(self):
        self.client.force_login(
            self.owner_user,
        )

        publication = Publication.objects.create(
            name="Delete Test Conference",
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description=(
                "Publication created for delete testing."
            ),
            organizer="RPMS Test Organization",
            venue="Kathmandu",
            submission_open_date=(
                self.today - timedelta(days=2)
            ),
            submission_deadline=(
                self.today + timedelta(days=10)
            ),
            review_deadline=(
                self.today + timedelta(days=20)
            ),
            event_date=(
                self.today + timedelta(days=30)
            ),
            location="Kathmandu",
            lifecycle_status=(
                Publication.LifecycleStatus.DRAFT
            ),
            created_by=self.owner_user,
            owner=self.owner_user,
        )

        publication_id = publication.pk

        response = self.client.post(
            reverse(
                "publication_delete",
                kwargs={
                    "pk": publication_id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("publication_list"),
        )

        self.assertFalse(
            Publication.objects.filter(
                pk=publication_id,
            ).exists()
        )

    def test_owner_cannot_delete_another_owners_publication(
        self,
    ):
        self.client.force_login(
            self.owner_user,
        )

        publication_id = (
            self.second_publication.pk
        )

        response = self.client.post(
            reverse(
                "publication_delete",
                kwargs={
                    "pk": publication_id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertTrue(
            Publication.objects.filter(
                pk=publication_id,
            ).exists()
        )


class AvailablePublicationTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.owner_user = User.objects.create_user(
            username="availableowner",
            password="StrongPass123!",
            role=User.Role.JOURNAL_OWNER,
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
            created_by=self.owner_user,
        )

        self.available_publication = (
            self.create_publication(
                name="Available Conference",
                lifecycle_status=(
                    Publication.LifecycleStatus.ACTIVE
                ),
                open_date=(
                    self.today
                    - timedelta(days=2)
                ),
                deadline=(
                    self.today
                    + timedelta(days=10)
                ),
            )
        )

        self.draft_publication = (
            self.create_publication(
                name="Draft Conference",
                lifecycle_status=(
                    Publication.LifecycleStatus.DRAFT
                ),
                open_date=(
                    self.today
                    - timedelta(days=2)
                ),
                deadline=(
                    self.today
                    + timedelta(days=10)
                ),
            )
        )

        self.archived_publication = (
            self.create_publication(
                name="Archived Conference",
                lifecycle_status=(
                    Publication.LifecycleStatus.ARCHIVED
                ),
                open_date=(
                    self.today
                    - timedelta(days=2)
                ),
                deadline=(
                    self.today
                    + timedelta(days=10)
                ),
            )
        )

        self.future_publication = (
            self.create_publication(
                name="Future Conference",
                lifecycle_status=(
                    Publication.LifecycleStatus.ACTIVE
                ),
                open_date=(
                    self.today
                    + timedelta(days=5)
                ),
                deadline=(
                    self.today
                    + timedelta(days=15)
                ),
            )
        )

        self.expired_publication = (
            self.create_publication(
                name="Expired Conference",
                lifecycle_status=(
                    Publication.LifecycleStatus.ACTIVE
                ),
                open_date=(
                    self.today
                    - timedelta(days=20)
                ),
                deadline=(
                    self.today
                    - timedelta(days=1)
                ),
            )
        )

    def create_publication(
        self,
        name,
        lifecycle_status,
        open_date,
        deadline,
    ):
        return Publication.objects.create(
            name=name,
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description=(
                "Publication availability test."
            ),
            organizer="RPMS Test Organization",
            venue="Online",
            submission_open_date=open_date,
            submission_deadline=deadline,
            review_deadline=(
                deadline + timedelta(days=10)
            ),
            event_date=(
                deadline + timedelta(days=20)
            ),
            location="Online",
            lifecycle_status=lifecycle_status,
            created_by=self.owner_user,
            owner=self.owner_user,
        )

    def test_author_sees_only_currently_available_publications(
        self,
    ):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("available_publications")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            (
                "publications/"
                "available_publications.html"
            ),
        )

        publications = response.context[
            "publications"
        ]

        self.assertIn(
            self.available_publication,
            publications,
        )

        self.assertNotIn(
            self.draft_publication,
            publications,
        )

        self.assertNotIn(
            self.archived_publication,
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

    def test_reviewer_cannot_view_available_publications(
        self,
    ):
        self.client.force_login(
            self.reviewer_user,
        )

        response = self.client.get(
            reverse("available_publications")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_owner_cannot_view_author_available_publications(
        self,
    ):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse("available_publications")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )