from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.system_admin = User.objects.create_superuser(
            username="systemadmin",
            password="StrongPass123!",
        )

        self.owner_user = User.objects.create_user(
            username="owneruser",
            password="StrongPass123!",
            role=User.Role.JOURNAL_OWNER,
        )

        self.editor_user = User.objects.create_user(
            username="editoruser",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            created_by=self.owner_user,
        )

        self.author_user = User.objects.create_user(
            username="authoruser",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

        self.reviewer_user = User.objects.create_user(
            username="revieweruser",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
            created_by=self.owner_user,
        )

    def test_home_page_loads_without_login(self):
        response = self.client.get(
            reverse("home")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "home.html",
        )

    def test_dashboard_redirect_requires_login(self):
        response = self.client.get(
            reverse("dashboard_redirect")
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next={reverse('dashboard_redirect')}"
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            expected_url,
        )

    def test_system_admin_is_redirected_to_django_admin(self):
        self.client.force_login(
            self.system_admin,
        )

        response = self.client.get(
            reverse("dashboard_redirect")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            "/admin/",
        )

    def test_journal_owner_is_redirected_to_owner_dashboard(
        self,
    ):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse("dashboard_redirect")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("journal_owner_dashboard"),
        )

    def test_editor_is_redirected_to_editor_dashboard(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse("dashboard_redirect")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("editor_dashboard"),
        )

    def test_author_is_redirected_to_author_dashboard(self):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("dashboard_redirect")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("author_dashboard"),
        )

    def test_reviewer_is_redirected_to_reviewer_dashboard(
        self,
    ):
        self.client.force_login(
            self.reviewer_user,
        )

        response = self.client.get(
            reverse("dashboard_redirect")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("reviewer_dashboard"),
        )

    def test_journal_owner_can_access_owner_dashboard(self):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse("journal_owner_dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "dashboard/journal_owner_dashboard.html",
        )

    def test_editor_can_access_editor_dashboard(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse("editor_dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "dashboard/editor_dashboard.html",
        )

    def test_author_can_access_author_dashboard(self):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("author_dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "dashboard/author_dashboard.html",
        )

    def test_reviewer_can_access_reviewer_dashboard(self):
        self.client.force_login(
            self.reviewer_user,
        )

        response = self.client.get(
            reverse("reviewer_dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "dashboard/reviewer_dashboard.html",
        )

    def test_author_cannot_access_editor_dashboard(self):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("editor_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_reviewer_cannot_access_author_dashboard(self):
        self.client.force_login(
            self.reviewer_user,
        )

        response = self.client.get(
            reverse("author_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_editor_cannot_access_owner_dashboard(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse("journal_owner_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_owner_cannot_access_reviewer_dashboard(self):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse("reviewer_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )