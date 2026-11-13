import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from publications.models import Publication

from .models import Paper, PaperVersion


User = get_user_model()


class TemporaryMediaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.temp_media = tempfile.TemporaryDirectory()
        cls.media_override = override_settings(
            MEDIA_ROOT=cls.temp_media.name
        )
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        cls.temp_media.cleanup()

        super().tearDownClass()


class PaperTestBase(TemporaryMediaTestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.admin_user = User.objects.create_user(
            username="paperadmin",
            password="StrongPass123!",
            role=User.Role.ADMIN,
        )

        self.author_user = User.objects.create_user(
            username="paperauthor",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

        self.second_author = User.objects.create_user(
            username="secondauthor",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

        self.reviewer_user = User.objects.create_user(
            username="paperreviewer",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
        )

        self.publication = Publication.objects.create(
            name="Open Research Conference",
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description="An open publication for paper tests.",
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
            status=Publication.Status.OPEN,
            created_by=self.admin_user,
        )

    def valid_pdf(self, filename="research-paper.pdf"):
        return SimpleUploadedFile(
            filename,
            b"%PDF-1.4 automated test paper",
            content_type="application/pdf",
        )

    def submission_data(self, filename="research-paper.pdf"):
        return {
            "publication": self.publication.pk,
            "title": "Automated Research Paper",
            "abstract": "This is an automated test abstract.",
            "keywords": "Django, testing, research",
            "research_category": "Computer Science",
            "paper_file": self.valid_pdf(filename),
        }

    def create_paper(
        self,
        author=None,
        status=Paper.Status.SUBMITTED,
        title="Existing Research Paper",
    ):
        return Paper.objects.create(
            publication=self.publication,
            corresponding_author=author or self.author_user,
            title=title,
            abstract="Existing paper abstract.",
            keywords="research, automation",
            research_category="Computer Science",
            status=status,
            submitted_at=timezone.now(),
        )


class PaperSubmissionTests(PaperTestBase):
    def test_author_can_open_submission_page(self):
        self.client.force_login(self.author_user)

        response = self.client.get(reverse("paper_submit"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "papers/paper_submit.html",
        )

    def test_author_can_submit_paper_and_create_version(self):
        self.client.force_login(self.author_user)

        response = self.client.post(
            reverse("paper_submit"),
            self.submission_data(),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("author_dashboard"),
        )

        paper = Paper.objects.get(
            title="Automated Research Paper"
        )

        self.assertEqual(
            paper.corresponding_author,
            self.author_user,
        )
        self.assertEqual(
            paper.status,
            Paper.Status.SUBMITTED,
        )
        self.assertIsNotNone(paper.submitted_at)

        version = PaperVersion.objects.get(paper=paper)

        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.uploaded_by, self.author_user)
        self.assertTrue(version.file.name.endswith(".pdf"))

    def test_non_pdf_upload_is_rejected(self):
        self.client.force_login(self.author_user)

        data = self.submission_data(filename="research-paper.txt")

        response = self.client.post(
            reverse("paper_submit"),
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Paper.objects.filter(
                title="Automated Research Paper"
            ).exists()
        )
        self.assertContains(
            response,
            "File extension",
        )

    def test_reviewer_cannot_access_submission_page(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.get(reverse("paper_submit"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_author_sees_only_own_submissions(self):
        own_paper = self.create_paper(
            author=self.author_user,
            title="Author Own Paper",
        )

        other_paper = self.create_paper(
            author=self.second_author,
            title="Another Author Paper",
        )

        self.client.force_login(self.author_user)

        response = self.client.get(
            reverse("my_submissions")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "papers/my_submissions.html",
        )

        papers = response.context["papers"]

        self.assertIn(own_paper, papers)
        self.assertNotIn(other_paper, papers)

    def test_author_cannot_view_another_authors_paper(self):
        other_paper = self.create_paper(
            author=self.second_author,
        )

        self.client.force_login(self.author_user)

        response = self.client.get(
            reverse(
                "paper_detail",
                kwargs={"pk": other_paper.pk},
            )
        )

        self.assertEqual(response.status_code, 404)


class AdminPaperWorkflowTests(PaperTestBase):
    def setUp(self):
        super().setUp()

        self.paper = self.create_paper()

    def test_admin_can_view_paper_list(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("admin_paper_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "papers/admin_paper_list.html",
        )
        self.assertContains(response, self.paper.title)

    def test_author_cannot_view_admin_paper_list(self):
        self.client.force_login(self.author_user)

        response = self.client.get(
            reverse("admin_paper_list")
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_admin_can_view_paper_detail(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "admin_paper_detail",
                kwargs={"pk": self.paper.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "papers/admin_paper_detail.html",
        )
        self.assertContains(response, self.paper.title)

    def test_admin_can_move_paper_to_initial_review(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "paper_initial_screening",
                kwargs={"pk": self.paper.pk},
            ),
            {
                "status": Paper.Status.UNDER_INITIAL_REVIEW,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_INITIAL_REVIEW,
        )

    def test_admin_can_mark_paper_ready_for_review(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "paper_initial_screening",
                kwargs={"pk": self.paper.pk},
            ),
            {
                "status": Paper.Status.READY_FOR_REVIEW,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.READY_FOR_REVIEW,
        )

    def test_final_decision_is_blocked_before_review_completion(
        self,
    ):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={"pk": self.paper.pk},
            ),
            {
                "status": Paper.Status.ACCEPTED,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.SUBMITTED,
        )

    def test_admin_can_accept_review_completed_paper(self):
        self.paper.status = Paper.Status.REVIEW_COMPLETED
        self.paper.save(update_fields=["status"])

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={"pk": self.paper.pk},
            ),
            {
                "status": Paper.Status.ACCEPTED,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.ACCEPTED,
        )

    def test_admin_can_reject_review_completed_paper(self):
        self.paper.status = Paper.Status.REVIEW_COMPLETED
        self.paper.save(update_fields=["status"])

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={"pk": self.paper.pk},
            ),
            {
                "status": Paper.Status.REJECTED,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.REJECTED,
        )

    def test_final_decision_cannot_change_after_acceptance(self):
        self.paper.status = Paper.Status.ACCEPTED
        self.paper.save(update_fields=["status"])

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={"pk": self.paper.pk},
            ),
            {
                "status": Paper.Status.REJECTED,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.ACCEPTED,
        )