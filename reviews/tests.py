from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from papers.models import Paper
from publications.models import Publication

from .models import ReviewerAssignment


User = get_user_model()


class ReviewerWorkflowTestBase(TestCase):
    def setUp(self):
        today = timezone.localdate()

        self.admin_user = User.objects.create_user(
            username="reviewadmin",
            password="StrongPass123!",
            role=User.Role.ADMIN,
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
        )

        self.second_reviewer = User.objects.create_user(
            username="reviewertwo",
            password="StrongPass123!",
            role=User.Role.REVIEWER,
            area_of_expertise="Artificial Intelligence",
        )

        self.publication = Publication.objects.create(
            name="Reviewer Test Conference",
            publication_type=(
                Publication.PublicationType.CONFERENCE
            ),
            description="Publication used for review tests.",
            submission_open_date=today - timedelta(days=5),
            submission_deadline=today + timedelta(days=10),
            review_deadline=today + timedelta(days=20),
            event_date=today + timedelta(days=30),
            location="Kathmandu",
            status=Publication.Status.OPEN,
            created_by=self.admin_user,
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

    def create_assignment(
        self,
        reviewer=None,
        status=ReviewerAssignment.Status.ASSIGNED,
    ):
        return ReviewerAssignment.objects.create(
            paper=self.paper,
            reviewer=reviewer or self.reviewer_user,
            assigned_by=self.admin_user,
            status=status,
        )


class ReviewerAssignmentCreationTests(ReviewerWorkflowTestBase):
    def test_admin_can_open_reviewer_assignment_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={"paper_pk": self.paper.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "reviews/reviewer_assignment_form.html",
        )

    def test_admin_can_assign_reviewer(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "reviewer_assignment_create",
                kwargs={"paper_pk": self.paper.pk},
            ),
            {
                "reviewer": self.reviewer_user.pk,
            },
        )

        self.assertEqual(response.status_code, 302)

        assignment = ReviewerAssignment.objects.get(
            paper=self.paper,
            reviewer=self.reviewer_user,
        )

        self.assertEqual(
            assignment.status,
            ReviewerAssignment.Status.ASSIGNED,
        )
        self.assertEqual(
            assignment.assigned_by,
            self.admin_user,
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_REVIEW,
        )

    def test_assignment_is_blocked_when_paper_is_not_ready(self):
        self.paper.status = Paper.Status.SUBMITTED
        self.paper.save(update_fields=["status"])

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "reviewer_assignment_create",
                kwargs={"paper_pk": self.paper.pk},
            ),
            {
                "reviewer": self.reviewer_user.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ReviewerAssignment.objects.filter(
                paper=self.paper,
                reviewer=self.reviewer_user,
            ).exists()
        )

    def test_author_cannot_assign_reviewer(self):
        self.client.force_login(self.author_user)

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={"paper_pk": self.paper.pk},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard_redirect"),
        )

    def test_already_assigned_reviewer_is_removed_from_form(self):
        self.create_assignment()

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "reviewer_assignment_create",
                kwargs={"paper_pk": self.paper.pk},
            )
        )

        reviewers = response.context["form"].fields[
            "reviewer"
        ].queryset

        self.assertNotIn(self.reviewer_user, reviewers)
        self.assertIn(self.second_reviewer, reviewers)


class ReviewerAssignmentResponseTests(ReviewerWorkflowTestBase):
    def setUp(self):
        super().setUp()

        self.paper.status = Paper.Status.UNDER_REVIEW
        self.paper.save(update_fields=["status"])

        self.assignment = self.create_assignment()

    def test_reviewer_sees_only_own_assignments(self):
        other_assignment = self.create_assignment(
            reviewer=self.second_reviewer,
        )

        self.client.force_login(self.reviewer_user)

        response = self.client.get(
            reverse("reviewer_assignment_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "reviews/assignment_list.html",
        )

        assignments = response.context["assignments"]

        self.assertIn(self.assignment, assignments)
        self.assertNotIn(other_assignment, assignments)

    def test_reviewer_cannot_view_another_reviewers_assignment(self):
        other_assignment = self.create_assignment(
            reviewer=self.second_reviewer,
        )

        self.client.force_login(self.reviewer_user)

        response = self.client.get(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": other_assignment.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_reviewer_can_accept_assignment(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
            ),
            {
                "action": "accept",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assignment.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.ACCEPTED,
        )
        self.assertIsNotNone(self.assignment.responded_at)

    def test_declining_only_assignment_returns_paper_to_ready(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
            ),
            {
                "action": "decline",
            },
        )

        self.assertEqual(response.status_code, 302)

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
            status=ReviewerAssignment.Status.ACCEPTED,
        )

        self.client.force_login(self.reviewer_user)

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
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
        completed_assignment = self.create_assignment(
            reviewer=self.second_reviewer,
            status=ReviewerAssignment.Status.COMPLETED,
        )
        completed_assignment.recommendation = (
            ReviewerAssignment.Recommendation.ACCEPT
        )
        completed_assignment.completed_at = timezone.now()
        completed_assignment.save()

        self.client.force_login(self.reviewer_user)

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
            ),
            {
                "action": "decline",
            },
        )

        self.paper.refresh_from_db()

        self.assertEqual(
            self.paper.status,
            Paper.Status.REVIEW_COMPLETED,
        )

    def test_assignment_cannot_be_completed_before_acceptance(self):
        self.client.force_login(self.reviewer_user)

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
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
        self.assertEqual(self.assignment.recommendation, "")
        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_REVIEW,
        )


class ReviewerCompletionTests(ReviewerWorkflowTestBase):
    def setUp(self):
        super().setUp()

        self.paper.status = Paper.Status.UNDER_REVIEW
        self.paper.save(update_fields=["status"])

        self.assignment = self.create_assignment(
            status=ReviewerAssignment.Status.ACCEPTED,
        )
        self.assignment.responded_at = timezone.now()
        self.assignment.save(update_fields=["responded_at"])

    def test_reviewer_can_complete_with_accept_recommendation(self):
        self.client.force_login(self.reviewer_user)

        response = self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
            ),
            {
                "action": "complete_accept",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.COMPLETED,
        )
        self.assertEqual(
            self.assignment.recommendation,
            ReviewerAssignment.Recommendation.ACCEPT,
        )
        self.assertIsNotNone(self.assignment.completed_at)
        self.assertEqual(
            self.paper.status,
            Paper.Status.REVIEW_COMPLETED,
        )

    def test_reviewer_can_complete_with_reject_recommendation(self):
        self.client.force_login(self.reviewer_user)

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
            ),
            {
                "action": "complete_reject",
            },
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()

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

    def test_completing_one_review_keeps_paper_under_review_when_active_exists(
        self,
    ):
        self.create_assignment(
            reviewer=self.second_reviewer,
            status=ReviewerAssignment.Status.ASSIGNED,
        )

        self.client.force_login(self.reviewer_user)

        self.client.post(
            reverse(
                "reviewer_assignment_detail",
                kwargs={"pk": self.assignment.pk},
            ),
            {
                "action": "complete_accept",
            },
        )

        self.assignment.refresh_from_db()
        self.paper.refresh_from_db()

        self.assertEqual(
            self.assignment.status,
            ReviewerAssignment.Status.COMPLETED,
        )
        self.assertEqual(
            self.paper.status,
            Paper.Status.UNDER_REVIEW,
        )