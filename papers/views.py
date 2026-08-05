from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from dashboard.decorators import role_required

from .forms import (
    FinalDecisionForm,
    InitialScreeningForm,
    PaperSubmissionForm,
)
from .models import Paper, PaperVersion


@role_required([User.Role.AUTHOR])
def paper_submit(request):
    if request.method == "POST":
        form = PaperSubmissionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            with transaction.atomic():
                paper = form.save(commit=False)
                paper.corresponding_author = request.user
                paper.status = Paper.Status.SUBMITTED
                paper.submitted_at = timezone.now()
                paper.save()

                PaperVersion.objects.create(
                    paper=paper,
                    version_number=1,
                    file=form.cleaned_data["paper_file"],
                    uploaded_by=request.user,
                )

            messages.success(
                request,
                "Research paper submitted successfully.",
            )

            return redirect("author_dashboard")
    else:
        form = PaperSubmissionForm()

    return render(
        request,
        "papers/paper_submit.html",
        {"form": form},
    )


@role_required([User.Role.AUTHOR])
def my_submissions(request):
    papers = (
        Paper.objects.filter(
            corresponding_author=request.user,
        )
        .select_related("publication")
        .order_by("-created_at")
    )

    return render(
        request,
        "papers/my_submissions.html",
        {"papers": papers},
    )


@role_required([User.Role.AUTHOR])
def paper_detail(request, pk):
    paper = get_object_or_404(
        Paper.objects.select_related(
            "publication",
        ).prefetch_related("versions"),
        pk=pk,
        corresponding_author=request.user,
    )

    return render(
        request,
        "papers/paper_detail.html",
        {"paper": paper},
    )

@role_required([User.Role.ADMIN])
def admin_paper_list(request):
    papers = (
        Paper.objects.select_related(
            "publication",
            "corresponding_author",
        )
        .all()
        .order_by("-submitted_at")
    )

    return render(
        request,
        "papers/admin_paper_list.html",
        {"papers": papers},
    )


@role_required([User.Role.ADMIN])
def admin_paper_detail(request, pk):
    paper = get_object_or_404(
        Paper.objects.select_related(
            "publication",
            "corresponding_author",
        ).prefetch_related(
            "versions",
            "reviewer_assignments__reviewer",
        ),
        pk=pk,
    )

    return render(
        request,
        "papers/admin_paper_detail.html",
        {"paper": paper},
    )

@role_required([User.Role.ADMIN])
def paper_initial_screening(request, pk):
    paper = get_object_or_404(Paper, pk=pk)

    allowed_statuses = [
        Paper.Status.SUBMITTED,
        Paper.Status.UNDER_INITIAL_REVIEW,
    ]

    if paper.status not in allowed_statuses:
        messages.warning(
            request,
            "Initial screening is no longer available for this paper.",
        )

        return redirect(
            "admin_paper_detail",
            pk=paper.pk,
        )

    if request.method == "POST":
        form = InitialScreeningForm(
            request.POST,
            instance=paper,
        )

        if form.is_valid():
            paper = form.save()

            messages.success(
                request,
                (
                    "Paper status updated to "
                    f"{paper.get_status_display()}."
                ),
            )

            return redirect(
                "admin_paper_detail",
                pk=paper.pk,
            )
    else:
        form = InitialScreeningForm(instance=paper)

    return render(
        request,
        "papers/paper_initial_screening.html",
        {
            "form": form,
            "paper": paper,
        },
    )

@role_required([User.Role.ADMIN])
def paper_final_decision(request, pk):
    paper = get_object_or_404(Paper, pk=pk)

    if paper.status != Paper.Status.REVIEW_COMPLETED:
        messages.warning(
            request,
            "The review must be completed before making the final decision.",
        )

        return redirect(
            "admin_paper_detail",
            pk=paper.pk,
        )

    if request.method == "POST":
        form = FinalDecisionForm(
            request.POST,
            instance=paper,
        )

        if form.is_valid():
            paper = form.save()

            messages.success(
                request,
                f"Paper has been {paper.get_status_display().lower()}.",
            )

            return redirect(
                "admin_paper_detail",
                pk=paper.pk,
            )
    else:
        form = FinalDecisionForm(instance=paper)

    return render(
        request,
        "papers/paper_final_decision.html",
        {
            "form": form,
            "paper": paper,
        },
    )