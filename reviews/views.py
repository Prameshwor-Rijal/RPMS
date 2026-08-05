from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from dashboard.decorators import role_required
from papers.models import Paper

from .forms import ReviewerAssignmentForm
from .models import ReviewerAssignment


@role_required([User.Role.ADMIN])
def reviewer_assignment_create(request, paper_pk):
    paper = get_object_or_404(Paper, pk=paper_pk)

    allowed_statuses = [
        Paper.Status.READY_FOR_REVIEW,
    ]

    if paper.status not in allowed_statuses:
        messages.warning(
            request,
            "Mark the paper as Ready for Reviewer Assignment first.",
        )

        return redirect(
            "admin_paper_detail",
            pk=paper.pk,
        )

    if request.method == "POST":
        form = ReviewerAssignmentForm(
            request.POST,
            paper=paper,
        )

        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.paper = paper
            assignment.assigned_by = request.user
            assignment.status = ReviewerAssignment.Status.ASSIGNED
            assignment.save()

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
                    "to review the paper."
                ),
            )

            return redirect(
                "admin_paper_detail",
                pk=paper.pk,
            )
    else:
        form = ReviewerAssignmentForm(paper=paper)

    return render(
        request,
        "reviews/reviewer_assignment_form.html",
        {
            "form": form,
            "paper": paper,
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
        )
        .order_by("-assigned_at")
    )

    return render(
        request,
        "reviews/assignment_list.html",
        {"assignments": assignments},
    )


@role_required([User.Role.REVIEWER])
def reviewer_assignment_detail(request, pk):
    assignment = get_object_or_404(
        ReviewerAssignment.objects.select_related(
            "paper",
            "paper__publication",
        ).prefetch_related(
            "paper__versions",
        ),
        pk=pk,
        reviewer=request.user,
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "accept":
            if assignment.status != ReviewerAssignment.Status.ASSIGNED:
                messages.warning(
                    request,
                    "You have already responded to this assignment.",
                )
            else:
                assignment.status = ReviewerAssignment.Status.ACCEPTED
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
            if assignment.status != ReviewerAssignment.Status.ASSIGNED:
                messages.warning(
                    request,
                    "You have already responded to this assignment.",
                )
            else:
                assignment.status = ReviewerAssignment.Status.DECLINED
                assignment.responded_at = timezone.now()
                assignment.save(
                    update_fields=[
                        "status",
                        "responded_at",
                    ]
                )

                active_assignments = (
                    assignment.paper.reviewer_assignments.filter(
                        status__in=[
                            ReviewerAssignment.Status.ASSIGNED,
                            ReviewerAssignment.Status.ACCEPTED,
                        ]
                    )
                )

                completed_assignments = (
                    assignment.paper.reviewer_assignments.filter(
                        status=ReviewerAssignment.Status.COMPLETED,
                    )
                )

                if active_assignments.exists():
                    assignment.paper.status = Paper.Status.UNDER_REVIEW
                elif completed_assignments.exists():
                    assignment.paper.status = Paper.Status.REVIEW_COMPLETED
                else:
                    assignment.paper.status = Paper.Status.READY_FOR_REVIEW

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
        ]:
            if assignment.status != ReviewerAssignment.Status.ACCEPTED:
                messages.warning(
                    request,
                    "Only an accepted assignment can be completed.",
                )
            else:
                if action == "complete_accept":
                    assignment.recommendation = (
                        ReviewerAssignment.Recommendation.ACCEPT
                    )
                else:
                    assignment.recommendation = (
                        ReviewerAssignment.Recommendation.REJECT
                    )

                assignment.status = ReviewerAssignment.Status.COMPLETED
                assignment.completed_at = timezone.now()

                assignment.save(
                    update_fields=[
                        "status",
                        "recommendation",
                        "completed_at",
                    ]
                )

                remaining_assignments = (
                    assignment.paper.reviewer_assignments.filter(
                        status__in=[
                            ReviewerAssignment.Status.ASSIGNED,
                            ReviewerAssignment.Status.ACCEPTED,
                        ]
                    )
                )

                if remaining_assignments.exists():
                    assignment.paper.status = Paper.Status.UNDER_REVIEW
                else:
                    assignment.paper.status = Paper.Status.REVIEW_COMPLETED

                assignment.paper.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                messages.success(
                    request,
                    "Review completed successfully.",
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
        {"assignment": assignment},
    )