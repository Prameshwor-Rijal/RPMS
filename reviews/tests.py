from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from papers.models import Paper, PaperVersion
from publications.models import Publication

from .models import ReviewRound, ReviewerAssignment


User = get_user_model()


class ReviewerWorkflowTestBase(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.owner_user = User.objects.create_user(
            username="reviewowner",
            password="StrongPass123!",
            role=User.Role.JOURNAL_OWNER,
        )

        self.editor_user = User.objects.create_user(
            username="revieweditor",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            created_by=self.owner_user,
        )

        self.author_user = User.objects.create_user(
            username="reviewauthor",
            password="StrongPass123!",
            role=User.Role.AUTHOR,
        )

        self.reviewer_user = User.objects.create_user(
            username="reviewerone",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
            area_of_expertise="Computer Science",
            created_by=self.owner_user,
        )

        self.second_reviewer = User.objects.create_user(
            username="reviewertwo",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
            area_of_expertise="Artificial Intelligence",
            created_by=self.owner_user,
        )

        self.other_owner = User.objects.create_user(
            username="otherreviewowner",
            password="StrongPass123!",
            role=User.Role.JOURNAL_OWNER,
        )

        self.other_reviewer = User.objects.create_user(
            username="outsidereviewer",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
            area_of_expertise="Data Science",
            created_by=self.other_owner,
        )

        self.publication = Publication.objects.create(
            name="Reviewer Test Conference",
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description="Publication used for review tests.",
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
            self.editor_user
        )

        self.paper = Paper.objects.create(
            publication=self.publication,
            corresponding_author=self.author_user,
            title="Reviewer Workflow Paper",
            abstract="Paper abstract for reviewer tests.",
            keywords="Django, reviewer, workflow",
            research_category="Computer Science",
            status=Paper.Status.READY_FOR_REVIEW,
            submitted_at=timezone.now(),
        )

        self.paper_version = PaperVersion.objects.create(
            paper=self.paper,
            version_number=1,
            file="papers/versions/reviewer-test.pdf",
            uploaded_by=self.author_user,
        )

        self.review_round = ReviewRound.objects.create(
            paper=self.paper,
            paper_version=self.paper_version,
            round_number=1,
            status=ReviewRound.Status.OPEN,
        )

    def create_assignment(
        self,
        reviewer=None,
        status=ReviewerAssignment.Status.ASSIGNED,
    ):
        return ReviewerAssignment.objects.create(
            paper=self.paper,
            review_round=self.review_round,
            reviewer=reviewer or self.reviewer_user,
            assigned_by=self.editor_user,
            status=status,
        )


class ReviewerAssignmentCreationTests(
    ReviewerWorkflowTestBase
):
    def test_editor_can_open_reviewer_assignment_form(
        self,
    ):
        self.client.force_login(
            self.editor_user
        )

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "reviews/reviewer_assignment_form.html",
        )

    def test_editor_can_assign_reviewer(self):
        self.client.force_login(
            self.editor_user
        )

        response = self.client.post(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            ),
            {
                "reviewer": self.reviewer_user.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        assignment = ReviewerAssignment.objects.get(
            paper=self.paper,
            review_round=self.review_round,
            reviewer=self.reviewer_user,
        )

        self.assertEqual(
            assignment.status,
            ReviewerAssignment.Status.ASSIGNED,
        )

        self.assertEqual(
            assignment.assigned_by,
            self.editor_user,
        )

        self.assertEqual(
            assignment.review_round,
            self.review_round,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_REVIEW,
        )

    def test_assignment_is_blocked_when_paper_is_not_ready(
        self,
    ):
        self.paper.status = Paper.Status.SUBMITTED

        self.paper.save(
            update_fields=["status"]
        )

        self.client.force_login(
            self.editor_user
        )

        response = self.client.post(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            ),
            {
                "reviewer": self.reviewer_user.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            ReviewerAssignment.objects.filter(
                paper=self.paper,
                review_round=self.review_round,
                reviewer=self.reviewer_user,
            ).exists()
        )

    def test_author_cannot_assign_reviewer(self):
        self.client.force_login(
            self.author_user
        )

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_owner_cannot_assign_reviewer(self):
        self.client.force_login(
            self.owner_user
        )

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_already_assigned_reviewer_is_removed_from_form(
        self,
    ):
        self.create_assignment()

        self.client.force_login(
            self.editor_user
        )

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            )
        )

        reviewers = response.context[
            "form"
        ].fields["reviewer"].queryset

        self.assertNotIn(
            self.reviewer_user,
            reviewers,
        )

        self.assertIn(
            self.second_reviewer,
            reviewers,
        )

    def test_reviewer_from_another_owner_is_not_available(
        self,
    ):
        self.client.force_login(
            self.editor_user
        )

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            )
        )

        reviewers = response.context[
            "form"
        ].fields["reviewer"].queryset

        self.assertIn(
            self.reviewer_user,
            reviewers,
        )

        self.assertIn(
            self.second_reviewer,
            reviewers,
        )

        self.assertNotIn(
            self.other_reviewer,
            reviewers,
        )


class ReviewerAssignmentResponseTests(
    ReviewerWorkflowTestBase
):
    def setUp(self):
        super().setUp()

        self.paper.status = (
            Paper.Status.UNDER_REVIEW
        )

        self.paper.save(
            update_fields=["status"]
        )

        self.assignment = (
            self.create_assignment()
        )

    def test_reviewer_sees_only_own_assignments(self):
        other_assignment = self.create_assignment(
            reviewer=self.second_reviewer,
        )

        self.client.force_login(
            self.reviewer_user
        )

        response = self.client.get(
            reverse("reviewer_assignment_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "reviews/assignment_list.html",
        )

        assignments = response.context[
            "assignments"
        ]

        self.assertIn(
            self.assignment,
            assignments,
        )

        self.assertNotIn(
            other_assignment,
            assignments,
        )

    def test_reviewer_cannot_view_another_reviewers_assignment(
        self,
    ):
        other_assignment = self.create_assignment(
            reviewer=self.second_reviewer,
        )

        self.client.force_login(
            self.reviewer_user
        )

        response = self.client.get(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": other_assignment.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_reviewer_can_accept_assignment(self):
        self.client.force_login(
            self.reviewer_user
        )

        response = self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "accept",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assignment.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.ACCEPTED,
        )

        self.assertIsNotNone(
            self.assignment.responded_at
        )

    def test_declining_only_assignment_returns_paper_to_ready(
        self,
    ):
        self.client.force_login(
            self.reviewer_user
        )

        response = self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "decline",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.DECLINED,
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.READY_FOR_REVIEW,
        )

    def test_decline_keeps_paper_under_review_when_active_assignment_exists(
        self,
    ):
        self.create_assignment(
            reviewer=self.second_reviewer,
            status=(
                ReviewerAssignment.Status.ACCEPTED
            ),
        )

        self.client.force_login(
            self.reviewer_user
        )

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "decline",
            },
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_REVIEW,
        )

    def test_decline_marks_review_completed_when_completed_review_exists(
        self,
    ):
        completed_assignment = (
            self.create_assignment(
                reviewer=self.second_reviewer,
                status=(
                    ReviewerAssignment.Status.COMPLETED
                ),
            )
        )

        completed_assignment.recommendation = (
            ReviewerAssignment.Recommendation.ACCEPT
        )

        completed_assignment.completed_at = (
            timezone.now()
        )

        completed_assignment.save()

        self.client.force_login(
            self.reviewer_user
        )

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "decline",
            },
        )

        self.paper.refresh_from_db()
        self.review_round.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.REVIEW_COMPLETED,
        )

        self.assertEqual(
            self.review_round.status,
            ReviewRound.Status.COMPLETED,
        )

    def test_assignment_cannot_be_completed_before_acceptance(
        self,
    ):
        self.client.force_login(
            self.reviewer_user
        )

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "complete_accept",
            },
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.ASSIGNED,
        )

        self.assertEqual(
            self.assignment.recommendation,
            "",
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_REVIEW,
        )


class ReviewerCompletionTests(
    ReviewerWorkflowTestBase
):
    def setUp(self):
        super().setUp()

        self.paper.status = (
            Paper.Status.UNDER_REVIEW
        )

        self.paper.save(
            update_fields=["status"]
        )

        self.assignment = self.create_assignment(
            status=(
                ReviewerAssignment.Status.ACCEPTED
            ),
        )

        self.assignment.responded_at = (
            timezone.now()
        )

        self.assignment.save(
            update_fields=[
                "responded_at",
            ]
        )

    def test_reviewer_can_complete_with_accept_recommendation(
        self,
    ):
        self.client.force_login(
            self.reviewer_user
        )

        response = self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "complete_accept",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()
        self.review_round.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.COMPLETED,
        )

        self.assertEqual(
            self.assignment.recommendation,
            ReviewerAssignment.Recommendation.ACCEPT,
        )

        self.assertIsNotNone(
            self.assignment.completed_at
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.REVIEW_COMPLETED,
        )

        self.assertEqual(
            self.review_round.status,
            ReviewRound.Status.COMPLETED,
        )

    def test_reviewer_can_complete_with_reject_recommendation(
        self,
    ):
        self.client.force_login(
            self.reviewer_user
        )

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "complete_reject",
            },
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()
        self.review_round.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.COMPLETED,
        )

        self.assertEqual(
            self.assignment.recommendation,
            ReviewerAssignment.Recommendation.REJECT,
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.REVIEW_COMPLETED,
        )

        self.assertEqual(
            self.review_round.status,
            ReviewRound.Status.COMPLETED,
        )

    def test_reviewer_can_request_revision(
        self,
    ):
        self.client.force_login(
            self.reviewer_user
        )

        response = self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "complete_revision",
                "comments": (
                    "Please improve the methodology "
                    "section."
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()
        self.review_round.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.COMPLETED,
        )

        self.assertEqual(
            self.assignment.recommendation,
            ReviewerAssignment.Recommendation.REVISION,
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.REVISION_REQUIRED,
        )

        self.assertEqual(
            self.review_round.status,
            ReviewRound.Status.REVISION_REQUIRED,
        )

    def test_completing_one_review_keeps_paper_under_review_when_active_exists(
        self,
    ):
        self.create_assignment(
            reviewer=self.second_reviewer,
            status=(
                ReviewerAssignment.Status.ASSIGNED
            ),
        )

        self.client.force_login(
            self.reviewer_user
        )

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={
                    "pk": self.assignment.pk,
                },
            ),
            {
                "action": "complete_accept",
            },
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()
        self.review_round.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.COMPLETED,
        )

        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_REVIEW,
        )

        self.assertEqual(
            self.review_round.status,
            ReviewRound.Status.OPEN,
        )


class ReviewerRoundReuseTests(
    ReviewerWorkflowTestBase
):
    def test_same_reviewer_can_be_used_in_later_round(
        self,
    ):
        first_assignment = (
            self.create_assignment()
        )

        first_assignment.status = (
            ReviewerAssignment.Status.COMPLETED
        )

        first_assignment.recommendation = (
            ReviewerAssignment.Recommendation.REVISION
        )

        first_assignment.completed_at = (
            timezone.now()
        )

        first_assignment.save()

        self.review_round.status = (
            ReviewRound.Status.REVISION_REQUIRED
        )

        self.review_round.save(
            update_fields=["status"]
        )

        version_two = PaperVersion.objects.create(
            paper=self.paper,
            version_number=2,
            file="papers/versions/reviewer-test-v2.pdf",
            uploaded_by=self.author_user,
        )

        round_two = ReviewRound.objects.create(
            paper=self.paper,
            paper_version=version_two,
            round_number=2,
            status=ReviewRound.Status.OPEN,
        )

        self.paper.status = (
            Paper.Status.READY_FOR_REVIEW
        )

        self.paper.save(
            update_fields=["status"]
        )

        self.client.force_login(
            self.editor_user
        )

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        reviewers = response.context[
            "form"
        ].fields["reviewer"].queryset

        self.assertIn(
            self.reviewer_user,
            reviewers,
        )

        self.client.post(
            reverse(
                "reviewer_assignment_create",
                kwargs={
                    "paper_pk": self.paper.pk,
                },
            ),
            {
                "reviewer": self.reviewer_user.pk,
            },
        )

        self.assertTrue(
            ReviewerAssignment.objects.filter(
                paper=self.paper,
                review_round=round_two,
                reviewer=self.reviewer_user,
            ).exists()
        )