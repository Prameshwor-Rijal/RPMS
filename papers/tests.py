import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from publications.models import Publication

from .models import (
    Copyediting,
    FinalDecision,
    Paper,
    PaperVersion,
)


User = get_user_model()


class TemporaryMediaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.temp_media = tempfile.TemporaryDirectory()

        cls.media_override = override_settings(
            MEDIA_ROOT=cls.temp_media.name,
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

        self.owner_user = User.objects.create_user(
            username="paperowner",
            password="StrongPass123!",
            role=User.Role.JOURNAL_OWNER,
        )

        self.editor_user = User.objects.create_user(
            username="papereditor",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            created_by=self.owner_user,
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
            created_by=self.owner_user,
        )

        self.unassigned_editor = User.objects.create_user(
            username="othereditor",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            created_by=self.owner_user,
        )

        self.publication = Publication.objects.create(
            name="Open Research Conference",
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description=(
                "An active conference for automated paper tests."
            ),
            organizer="RPMS Test Organization",
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

    def valid_pdf(
        self,
        filename="research-paper.pdf",
    ):
        return SimpleUploadedFile(
            filename,
            b"%PDF-1.4 automated test paper",
            content_type="application/pdf",
        )

    def submission_data(
        self,
        filename="research-paper.pdf",
    ):
        return {
            "publication": self.publication.pk,
            "title": "Automated Research Paper",
            "abstract": (
                "This is an automated test abstract."
            ),
            "keywords": (
                "Django, testing, research"
            ),
            "research_category": (
                "Computer Science"
            ),
            "paper_file": self.valid_pdf(
                filename,
            ),
        }

    def create_paper(
        self,
        author=None,
        status=Paper.Status.SUBMITTED,
        title="Existing Research Paper",
        publication=None,
    ):
        return Paper.objects.create(
            publication=(
                publication
                or self.publication
            ),
            corresponding_author=(
                author
                or self.author_user
            ),
            title=title,
            abstract=(
                "Existing paper abstract."
            ),
            keywords=(
                "research, automation"
            ),
            research_category=(
                "Computer Science"
            ),
            status=status,
            submitted_at=timezone.now(),
        )

    def create_version(
        self,
        paper,
        version_number=1,
        uploaded_by=None,
        filename=None,
    ):
        if filename is None:
            filename = (
                f"version-{version_number}.pdf"
            )

        return PaperVersion.objects.create(
            paper=paper,
            version_number=version_number,
            file=self.valid_pdf(filename),
            uploaded_by=(
                uploaded_by
                or paper.corresponding_author
            ),
        )


class PaperSubmissionTests(PaperTestBase):
    def test_author_can_open_submission_page(self):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("paper_submit")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "papers/paper_submit.html",
        )

    def test_author_can_submit_paper_and_create_version(self):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.post(
            reverse("paper_submit"),
            self.submission_data(),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("author_dashboard"),
        )

        paper = Paper.objects.get(
            title="Automated Research Paper",
        )

        self.assertEqual(
            paper.corresponding_author,
            self.author_user,
        )

        self.assertEqual(
            paper.publication,
            self.publication,
        )

        self.assertEqual(
            paper.status,
            Paper.Status.SUBMITTED,
        )

        self.assertIsNotNone(
            paper.submitted_at,
        )

        version = PaperVersion.objects.get(
            paper=paper,
        )

        self.assertEqual(
            version.version_number,
            1,
        )

        self.assertEqual(
            version.uploaded_by,
            self.author_user,
        )

        self.assertTrue(
            version.file.name.endswith(
                ".pdf"
            )
        )

    def test_non_pdf_upload_is_rejected(self):
        self.client.force_login(
            self.author_user,
        )

        data = self.submission_data(
            filename="research-paper.txt",
        )

        response = self.client.post(
            reverse("paper_submit"),
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Paper.objects.filter(
                title=(
                    "Automated Research Paper"
                )
            ).exists()
        )

        self.assertContains(
            response,
            "File extension",
        )

    def test_invalid_pdf_content_is_rejected(self):
        self.client.force_login(
            self.author_user,
        )

        invalid_file = SimpleUploadedFile(
            "fake-paper.pdf",
            b"This is not actually a PDF.",
            content_type="application/pdf",
        )

        data = self.submission_data()
        data["paper_file"] = invalid_file

        response = self.client.post(
            reverse("paper_submit"),
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Paper.objects.filter(
                title=(
                    "Automated Research Paper"
                )
            ).exists()
        )

        self.assertContains(
            response,
            "not a valid PDF",
        )

    def test_reviewer_cannot_access_submission_page(self):
        self.client.force_login(
            self.reviewer_user,
        )

        response = self.client.get(
            reverse("paper_submit")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_editor_cannot_access_submission_page(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse("paper_submit")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

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

        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("my_submissions")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "papers/my_submissions.html",
        )

        papers = response.context[
            "papers"
        ]

        self.assertIn(
            own_paper,
            papers,
        )

        self.assertNotIn(
            other_paper,
            papers,
        )

    def test_author_can_view_own_paper(self):
        paper = self.create_paper(
            author=self.author_user,
        )

        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse(
                "paper_detail",
                kwargs={
                    "pk": paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "papers/paper_detail.html",
        )

        self.assertContains(
            response,
            paper.title,
        )

    def test_author_cannot_view_another_authors_paper(self):
        other_paper = self.create_paper(
            author=self.second_author,
        )

        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse(
                "paper_detail",
                kwargs={
                    "pk": other_paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class EditorPaperWorkflowTests(PaperTestBase):
    def setUp(self):
        super().setUp()

        self.paper = self.create_paper()

    def test_editor_can_view_assigned_paper_list(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse("editor_paper_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "papers/editor_paper_list.html",
        )

        self.assertContains(
            response,
            self.paper.title,
        )

    def test_author_cannot_view_editor_paper_list(self):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse("editor_paper_list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_reviewer_cannot_view_editor_paper_list(self):
        self.client.force_login(
            self.reviewer_user,
        )

        response = self.client.get(
            reverse("editor_paper_list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_editor_can_view_assigned_paper_detail(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse(
                "editor_paper_detail",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "papers/editor_paper_detail.html",
        )

        self.assertContains(
            response,
            self.paper.title,
        )

    def test_unassigned_editor_cannot_view_paper_detail(self):
        self.client.force_login(
            self.unassigned_editor,
        )

        response = self.client.get(
            reverse(
                "editor_paper_detail",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_editor_can_open_initial_screening_page(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse(
                "editor_paper_screening",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "papers/editor_paper_screening.html",
        )

    def test_editor_can_move_paper_to_initial_review(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.post(
            reverse(
                "editor_paper_screening",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": (
                    Paper.Status
                    .UNDER_INITIAL_REVIEW
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse(
                "editor_paper_detail",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_INITIAL_REVIEW,
        )

    def test_editor_can_mark_paper_ready_for_review(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.post(
            reverse(
                "editor_paper_screening",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": (
                    Paper.Status.READY_FOR_REVIEW
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.READY_FOR_REVIEW,
        )

    def test_editor_can_reject_during_initial_screening(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.post(
            reverse(
                "editor_paper_screening",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": Paper.Status.REJECTED,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.REJECTED,
        )

    def test_unassigned_editor_cannot_screen_paper(self):
        self.client.force_login(
            self.unassigned_editor,
        )

        response = self.client.get(
            reverse(
                "editor_paper_screening",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class FinalDecisionTests(PaperTestBase):
    def setUp(self):
        super().setUp()

        self.paper = self.create_paper()

    def test_final_decision_is_blocked_before_review_completion(
        self,
    ):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": Paper.Status.ACCEPTED,
                "note": "Accept this paper.",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.SUBMITTED,
        )

        self.assertFalse(
            FinalDecision.objects.filter(
                paper=self.paper,
            ).exists()
        )

    def test_editor_can_accept_review_completed_paper(self):
        self.paper.status = (
            Paper.Status.REVIEW_COMPLETED
        )

        self.paper.save(
            update_fields=[
                "status",
            ]
        )

        self.client.force_login(
            self.editor_user,
        )

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": Paper.Status.ACCEPTED,
                "note": (
                    "The paper is ready "
                    "for publication processing."
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.ACCEPTED,
        )

        decision = FinalDecision.objects.get(
            paper=self.paper,
        )

        self.assertEqual(
            decision.decision,
            FinalDecision.Decision.ACCEPTED,
        )

        self.assertEqual(
            decision.decided_by,
            self.editor_user,
        )

        self.assertEqual(
            decision.note,
            (
                "The paper is ready "
                "for publication processing."
            ),
        )

    def test_editor_can_reject_review_completed_paper(self):
        self.paper.status = (
            Paper.Status.REVIEW_COMPLETED
        )

        self.paper.save(
            update_fields=[
                "status",
            ]
        )

        self.client.force_login(
            self.editor_user,
        )

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": Paper.Status.REJECTED,
                "note": (
                    "The paper does not meet "
                    "the publication requirements."
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.REJECTED,
        )

        decision = FinalDecision.objects.get(
            paper=self.paper,
        )

        self.assertEqual(
            decision.decision,
            FinalDecision.Decision.REJECTED,
        )

        self.assertEqual(
            decision.decided_by,
            self.editor_user,
        )

    def test_final_decision_cannot_change_after_acceptance(self):
        self.paper.status = (
            Paper.Status.ACCEPTED
        )

        self.paper.save(
            update_fields=[
                "status",
            ]
        )

        FinalDecision.objects.create(
            paper=self.paper,
            decision=(
                FinalDecision.Decision.ACCEPTED
            ),
            decided_by=self.editor_user,
            note="Accepted decision.",
        )

        self.client.force_login(
            self.editor_user,
        )

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": Paper.Status.REJECTED,
                "note": "Attempted change.",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        decision = FinalDecision.objects.get(
            paper=self.paper,
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.ACCEPTED,
        )

        self.assertEqual(
            decision.decision,
            FinalDecision.Decision.ACCEPTED,
        )

        self.assertEqual(
            decision.note,
            "Accepted decision.",
        )

    def test_unassigned_editor_cannot_make_final_decision(self):
        self.paper.status = (
            Paper.Status.REVIEW_COMPLETED
        )

        self.paper.save(
            update_fields=[
                "status",
            ]
        )

        self.client.force_login(
            self.unassigned_editor,
        )

        response = self.client.post(
            reverse(
                "paper_final_decision",
                kwargs={
                    "pk": self.paper.pk,
                },
            ),
            {
                "status": Paper.Status.ACCEPTED,
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.REVIEW_COMPLETED,
        )

        self.assertFalse(
            FinalDecision.objects.filter(
                paper=self.paper,
            ).exists()
        )


class CopyeditingWorkflowTests(PaperTestBase):
    def setUp(self):
        super().setUp()

        self.paper = self.create_paper(
            status=Paper.Status.ACCEPTED,
            title="Accepted Copyediting Paper",
        )

        self.original_version = self.create_version(
            self.paper,
            version_number=1,
        )

        FinalDecision.objects.create(
            paper=self.paper,
            decision=FinalDecision.Decision.ACCEPTED,
            decided_by=self.editor_user,
            note="Accepted for copyediting.",
        )

    def start_copyediting(self):
        self.client.force_login(
            self.editor_user,
        )

        return self.client.post(
            reverse(
                "start_copyediting",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

    def test_editor_can_start_copyediting_for_accepted_paper(self):
        response = self.start_copyediting()

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.COPYEDITING,
        )

        copyediting = Copyediting.objects.get(
            paper=self.paper,
        )

        self.assertEqual(
            copyediting.status,
            Copyediting.Status.IN_PROGRESS,
        )

        self.assertEqual(
            copyediting.started_by,
            self.editor_user,
        )

    def test_editor_can_complete_copyediting_without_correction(self):
        self.start_copyediting()

        response = self.client.post(
            reverse(
                "complete_copyediting",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()

        copyediting = Copyediting.objects.get(
            paper=self.paper,
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.READY_FOR_PRODUCTION,
        )

        self.assertEqual(
            copyediting.status,
            Copyediting.Status.COMPLETED,
        )

        self.assertEqual(
            copyediting.completed_by,
            self.editor_user,
        )

        self.assertIsNotNone(
            copyediting.completed_at,
        )

    def test_copyediting_cannot_complete_while_correction_required(
        self,
    ):
        self.start_copyediting()

        copyediting = Copyediting.objects.get(
            paper=self.paper,
        )

        copyediting.status = (
            Copyediting.Status.CORRECTION_REQUIRED
        )

        copyediting.correction_note = (
            "Please correct formatting and references."
        )

        copyediting.correction_requested_at = (
            timezone.now()
        )

        copyediting.save(
            update_fields=[
                "status",
                "correction_note",
                "correction_requested_at",
            ]
        )

        self.paper.status = (
            Paper.Status.COPYEDITING_CORRECTION_REQUIRED
        )

        self.paper.save(
            update_fields=[
                "status",
            ]
        )

        response = self.client.post(
            reverse(
                "complete_copyediting",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()
        copyediting.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.COPYEDITING_CORRECTION_REQUIRED,
        )

        self.assertEqual(
            copyediting.status,
            Copyediting.Status.CORRECTION_REQUIRED,
        )

        self.assertIsNone(
            copyediting.completed_at,
        )

    def test_editor_can_complete_after_author_correction_submission(
        self,
    ):
        self.start_copyediting()

        corrected_version = self.create_version(
            self.paper,
            version_number=2,
            uploaded_by=self.author_user,
            filename="corrected-version.pdf",
        )

        copyediting = Copyediting.objects.get(
            paper=self.paper,
        )

        copyediting.status = (
            Copyediting.Status.CORRECTION_SUBMITTED
        )

        copyediting.corrected_version = (
            corrected_version
        )

        copyediting.correction_submitted_at = (
            timezone.now()
        )

        copyediting.author_note = (
            "Requested corrections have been completed."
        )

        copyediting.save(
            update_fields=[
                "status",
                "corrected_version",
                "correction_submitted_at",
                "author_note",
            ]
        )

        self.paper.status = (
            Paper.Status.COPYEDITING
        )

        self.paper.save(
            update_fields=[
                "status",
            ]
        )

        response = self.client.post(
            reverse(
                "complete_copyediting",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()
        copyediting.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.READY_FOR_PRODUCTION,
        )

        self.assertEqual(
            copyediting.status,
            Copyediting.Status.COMPLETED,
        )

        self.assertEqual(
            copyediting.corrected_version,
            corrected_version,
        )

        self.assertEqual(
            copyediting.completed_by,
            self.editor_user,
        )

        self.assertIsNotNone(
            copyediting.completed_at,
        )

    def test_correction_submission_without_version_cannot_complete(
        self,
    ):
        self.start_copyediting()

        copyediting = Copyediting.objects.get(
            paper=self.paper,
        )

        copyediting.status = (
            Copyediting.Status.CORRECTION_SUBMITTED
        )

        copyediting.correction_submitted_at = (
            timezone.now()
        )

        copyediting.save(
            update_fields=[
                "status",
                "correction_submitted_at",
            ]
        )

        response = self.client.post(
            reverse(
                "complete_copyediting",
                kwargs={
                    "pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.paper.refresh_from_db()
        copyediting.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.COPYEDITING,
        )

        self.assertEqual(
            copyediting.status,
            Copyediting.Status.CORRECTION_SUBMITTED,
        )

        self.assertIsNone(
            copyediting.completed_at,
        )


class PaperVersionAccessTests(PaperTestBase):
    def setUp(self):
        super().setUp()

        self.paper = self.create_paper()

        self.version = self.create_version(
            self.paper,
        )

    def test_author_can_access_own_paper_version(self):
        self.client.force_login(
            self.author_user,
        )

        response = self.client.get(
            reverse(
                "paper_version_file",
                kwargs={
                    "version_id": self.version.pk,
                },
            )
        )

        try:
            self.assertEqual(
                response.status_code,
                200,
            )

            self.assertEqual(
                response["Content-Type"],
                "application/pdf",
            )

        finally:
            response.close()

    def test_editor_can_access_assigned_paper_version(self):
        self.client.force_login(
            self.editor_user,
        )

        response = self.client.get(
            reverse(
                "paper_version_file",
                kwargs={
                    "version_id": self.version.pk,
                },
            )
        )

        try:
            self.assertEqual(
                response.status_code,
                200,
            )

        finally:
            response.close()

    def test_owner_can_access_owned_publication_paper_version(
        self,
    ):
        self.client.force_login(
            self.owner_user,
        )

        response = self.client.get(
            reverse(
                "paper_version_file",
                kwargs={
                    "version_id": self.version.pk,
                },
            )
        )

        try:
            self.assertEqual(
                response.status_code,
                200,
            )

        finally:
            response.close()

    def test_other_author_cannot_access_paper_version(self):
        self.client.force_login(
            self.second_author,
        )

        response = self.client.get(
            reverse(
                "paper_version_file",
                kwargs={
                    "version_id": self.version.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_unassigned_editor_cannot_access_paper_version(self):
        self.client.force_login(
            self.unassigned_editor,
        )

        response = self.client.get(
            reverse(
                "paper_version_file",
                kwargs={
                    "version_id": self.version.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )