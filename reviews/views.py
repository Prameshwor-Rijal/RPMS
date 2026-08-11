from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from dashboard.decorators import role_required
from papers.models import Paper

from .forms import ReviewerAssignmentForm
from .models import ReviewRound, ReviewerAssignment


@role_required([User.Role.EDITOR])
def reviewer_assignment_create(request, paper_pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__editors=request.user,
        )
        .select_related(
            "publication",
        )
        .prefetch_related(
            "versions",
            "review_rounds",
        ),
        pk=paper_pk,
    )

    allowed_statuses = [
        Paper.Status.READY_FOR_REVIEW,
        Paper.Status.UNDER_REVIEW,
    ]

    if paper.status not in allowed_statuses:
        messages.warning(
            request,
            (
                "Reviewers can only be assigned to papers "
                "that are ready for review or already under review."
            ),
        )

        return redirect(
            "admin_paper_detail",
            pk=paper.pk,
        )

    latest_version = (
        paper.versions.order_by(
            "-version_number",
        ).first()
    )

    if latest_version is None:
        messages.error(
            request,
            "This paper does not have a manuscript version to review.",
        )

        return redirect(
            "admin_paper_detail",
            pk=paper.pk,
        )

    review_round = (
        ReviewRound.objects.filter(
            paper=paper,
            paper_version=latest_version,
        ).first()
    )

    if review_round is None:
        latest_round_number = (
            paper.review_rounds.order_by(
                "-round_number",
            )
            .values_list(
                "round_number",
                flat=True,
            )
            .first()
        )

        next_round_number = (
            latest_round_number + 1
            if latest_round_number
            else 1
        )

        review_round = ReviewRound.objects.create(
            paper=paper,
            paper_version=latest_version,
            round_number=next_round_number,
            status=ReviewRound.Status.OPEN,
        )

    if review_round.status != ReviewRound.Status.OPEN:
        messages.warning(
            request,
            "Reviewers cannot be assigned to a completed review round.",
        )

        return redirect(
            "admin_paper_detail",
            pk=paper.pk,
        )

    if request.method == "POST":
        form = ReviewerAssignmentForm(
            request.POST,
            review_round=review_round,
        )

        if form.is_valid():
            assignment = form.save(commit=False)

            assignment.paper = paper
            assignment.review_round = review_round
            assignment.assigned_by = request.user
            assignment.status = (
                ReviewerAssignment.Status.ASSIGNED
            )

            assignment.save()

            if paper.status == Paper.Status.READY_FOR_REVIEW:
                paper.status = Paper.Status.UNDER_REVIEW

                paper.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            messages.success(
                request,
                (
                    f"{assignment.reviewer.username} was assigned "
                    f"to Review Round {review_round.round_number}."
                ),
            )

            return redirect(
                "admin_paper_detail",
                pk=paper.pk,
            )

    else:
        form = ReviewerAssignmentForm(
            review_round=review_round,
        )

    return render(
        request,
        "reviews/reviewer_assignment_form.html",
        {
            "form": form,
            "paper": paper,
            "review_round": review_round,
        },
    )


@role_required([User.Role.REVIEWER])
def reviewer_assignment_list(request):
    assignments = (
        ReviewerAssignment.objects.filter(
            reviewer=request.user,
        )
        .select_related(
            "paper",
            "paper__publication",
            "review_round",
            "review_round__paper_version",
        )
        .order_by(
            "-assigned_at",
        )
    )

    return render(
        request,
        "reviews/assignment_list.html",
        {
            "assignments": assignments,
        },
    )


@role_required([User.Role.REVIEWER])
def reviewer_assignment_detail(request, pk):
    assignment = get_object_or_404(
        ReviewerAssignment.objects.select_related(
            "paper",
            "paper__publication",
            "review_round",
            "review_round__paper_version",
        ),
        pk=pk,
        reviewer=request.user,
    )

    review_round = assignment.review_round

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "accept":
            if (
                assignment.status
                != ReviewerAssignment.Status.ASSIGNED
            ):
                messages.warning(
                    request,
                    "You have already responded to this assignment.",
                )

            else:
                assignment.status = (
                    ReviewerAssignment.Status.ACCEPTED
                )

                assignment.responded_at = timezone.now()

                assignment.save(
                    update_fields=[
                        "status",
                        "responded_at",
                    ]
                )

                messages.success(
                    request,
                    "Review assignment accepted successfully.",
                )

        elif action == "decline":
            if (
                assignment.status
                != ReviewerAssignment.Status.ASSIGNED
            ):
                messages.warning(
                    request,
                    "You have already responded to this assignment.",
                )

            else:
                assignment.status = (
                    ReviewerAssignment.Status.DECLINED
                )

                assignment.responded_at = timezone.now()

                assignment.save(
                    update_fields=[
                        "status",
                        "responded_at",
                    ]
                )

                active_assignments = (
                    review_round.reviewer_assignments.filter(
                        status__in=[
                            ReviewerAssignment.Status.ASSIGNED,
                            ReviewerAssignment.Status.ACCEPTED,
                        ]
                    )
                )

                completed_assignments = (
                    review_round.reviewer_assignments.filter(
                        status=ReviewerAssignment.Status.COMPLETED,
                    )
                )

                if active_assignments.exists():
                    assignment.paper.status = (
                        Paper.Status.UNDER_REVIEW
                    )

                elif completed_assignments.exists():
                    revision_requested = (
                        completed_assignments.filter(
                            recommendation=(
                                ReviewerAssignment
                                .Recommendation
                                .REVISION
                            )
                        ).exists()
                    )

                    if revision_requested:
                        review_round.status = (
                            ReviewRound.Status.REVISION_REQUIRED
                        )

                        assignment.paper.status = (
                            Paper.Status.REVISION_REQUIRED
                        )

                    else:
                        review_round.status = (
                            ReviewRound.Status.COMPLETED
                        )

                        assignment.paper.status = (
                            Paper.Status.REVIEW_COMPLETED
                        )

                    review_round.completed_at = timezone.now()

                    review_round.save(
                        update_fields=[
                            "status",
                            "completed_at",
                        ]
                    )

                else:
                    assignment.paper.status = (
                        Paper.Status.READY_FOR_REVIEW
                    )

                assignment.paper.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                messages.success(
                    request,
                    "Review assignment declined.",
                )

        elif action in [
            "complete_accept",
            "complete_reject",
            "complete_revision",
        ]:
            if (
                assignment.status
                != ReviewerAssignment.Status.ACCEPTED
            ):
                messages.warning(
                    request,
                    "Only an accepted assignment can be completed.",
                )

            else:
                comments = request.POST.get(
                    "comments",
                    "",
                ).strip()

                if (
                    action == "complete_revision"
                    and not comments
                ):
                    messages.error(
                        request,
                        (
                            "Please provide comments explaining "
                            "the required revision."
                        ),
                    )

                    return redirect(
                        "reviewer_assignment_detail",
                        pk=assignment.pk,
                    )

                if action == "complete_accept":
                    assignment.recommendation = (
                        ReviewerAssignment.Recommendation.ACCEPT
                    )

                elif action == "complete_reject":
                    assignment.recommendation = (
                        ReviewerAssignment.Recommendation.REJECT
                    )

                else:
                    assignment.recommendation = (
                        ReviewerAssignment.Recommendation.REVISION
                    )

                assignment.comments = comments
                assignment.status = (
                    ReviewerAssignment.Status.COMPLETED
                )

                assignment.completed_at = timezone.now()

                assignment.save(
                    update_fields=[
                        "status",
                        "recommendation",
                        "comments",
                        "completed_at",
                    ]
                )

                remaining_assignments = (
                    review_round.reviewer_assignments.filter(
                        status__in=[
                            ReviewerAssignment.Status.ASSIGNED,
                            ReviewerAssignment.Status.ACCEPTED,
                        ]
                    )
                )

                if remaining_assignments.exists():
                    assignment.paper.status = (
                        Paper.Status.UNDER_REVIEW
                    )

                else:
                    revision_requested = (
                        review_round
                        .reviewer_assignments
                        .filter(
                            status=(
                                ReviewerAssignment.Status.COMPLETED
                            ),
                            recommendation=(
                                ReviewerAssignment
                                .Recommendation
                                .REVISION
                            ),
                        )
                        .exists()
                    )

                    if revision_requested:
                        review_round.status = (
                            ReviewRound.Status.REVISION_REQUIRED
                        )

                        assignment.paper.status = (
                            Paper.Status.REVISION_REQUIRED
                        )

                    else:
                        review_round.status = (
                            ReviewRound.Status.COMPLETED
                        )

                        assignment.paper.status = (
                            Paper.Status.REVIEW_COMPLETED
                        )

                    review_round.completed_at = timezone.now()

                    review_round.save(
                        update_fields=[
                            "status",
                            "completed_at",
                        ]
                    )

                assignment.paper.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                messages.success(
                    request,
                    "Review submitted successfully.",
                )

        else:
            messages.error(
                request,
                "Invalid assignment response.",
            )

        return redirect(
            "reviewer_assignment_detail",
            pk=assignment.pk,
        )

    return render(
        request,
        "reviews/assignment_detail.html",
        {
            "assignment": assignment,
            "review_round": review_round,
        },
    )