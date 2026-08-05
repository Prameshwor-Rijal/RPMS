from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AuthorRegistrationTests(TestCase):
    def setUp(self):
        self.register_url = reverse("register")

    def test_registration_page_loads(self):
        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_valid_registration_creates_author(self):
        response = self.client.post(
            self.register_url,
            {
                "first_name": "Test",
                "last_name": "Author",
                "username": "testauthor",
                "email": "testauthor@example.com",
                "institution": "Test University",
                "area_of_expertise": "Computer Science",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_redirect"))

        user = User.objects.get(username="testauthor")

        self.assertEqual(user.role, User.Role.AUTHOR)
        self.assertEqual(user.email, "testauthor@example.com")
        self.assertEqual(user.institution, "Test University")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_registration_password_mismatch_does_not_create_user(self):
        response = self.client.post(
            self.register_url,
            {
                "first_name": "Test",
                "last_name": "Author",
                "username": "invalidauthor",
                "email": "invalid@example.com",
                "institution": "Test University",
                "area_of_expertise": "Computer Science",
                "password1": "StrongPass123!",
                "password2": "DifferentPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username="invalidauthor").exists()
        )

    def test_logged_in_user_cannot_open_registration_page(self):
        user = User.objects.create_user(
            username="existingauthor",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

        self.client.force_login(user)

        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_redirect"))


class UserLoginTests(TestCase):
    def setUp(self):
        self.login_url = reverse("login")

        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_valid_login_authenticates_user(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "loginuser",
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_invalid_login_does_not_authenticate_user(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "loginuser",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(
            response,
            "Please enter a correct username and password",
        )

    def test_authenticated_user_is_redirected_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 302)