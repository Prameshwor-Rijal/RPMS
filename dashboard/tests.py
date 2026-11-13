from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="adminuser",
            password="StrongPass123!",
            role=User.Role.ADMIN,
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
        )

    def test_home_page_loads_without_login(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_dashboard_redirect_requires_login(self):
        response = self.client.get(reverse("dashboard_redirect"))

        expected_url = (
            f"{reverse('login')}?next={reverse('dashboard_redirect')}"
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

    def test_author_is_redirected_to_author_dashboard(self):
        self.client.force_login(self.author_user)

        response = self.client.get(reverse("dashboard_redirect"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("author_dashboard"))

    def test_reviewer_is_redirected_to_reviewer_dashboard(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.get(reverse("dashboard_redirect"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("reviewer_dashboard"))

    def test_admin_is_redirected_to_admin_dashboard(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("dashboard_redirect"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_dashboard"))

    def test_author_can_access_author_dashboard(self):
        self.client.force_login(self.author_user)

        response = self.client.get(reverse("author_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "dashboard/author_dashboard.html",
        )

    def test_reviewer_can_access_reviewer_dashboard(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.get(reverse("reviewer_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "dashboard/reviewer_dashboard.html",
        )

    def test_admin_can_access_admin_dashboard(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "dashboard/admin_dashboard.html",
        )

    def test_author_cannot_access_admin_dashboard(self):
        self.client.force_login(self.author_user)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_redirect"))

    def test_reviewer_cannot_access_author_dashboard(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.get(reverse("author_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_redirect"))

    def test_admin_cannot_access_reviewer_dashboard(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("reviewer_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_redirect"))