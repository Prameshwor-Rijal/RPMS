from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from dashboard.decorators import role_required

from .forms import (
    CopyeditingCorrectionForm,
    CopyeditingSubmissionForm,
    FinalDecisionForm,
    InitialScreeningForm,
    PaperRevisionForm,
    PaperSubmissionForm,
)
from .models import (
    Copyediting,
    FinalDecision,
    Paper,
    PaperVersion,
    Production,
)


@login_required
def paper_version_file(request, version_id):
    version = get_object_or_404(
        PaperVersion.objects.select_related(
            "paper",
            "paper__publication",
            "paper__corresponding_author",
        ),
        pk=version_id,
    )

    paper = version.paper
    user = request.user

    has_access = False

    if user.is_superuser:
        has_access = True

    elif user.role == User.Role.AUTHOR:
        has_access = (
            paper.corresponding_author_id
            == user.id
        )

    elif user.role == User.Role.EDITOR:
        has_access = (
            paper.publication.editors.filter(
                pk=user.pk,
            ).exists()
        )

    elif user.role == User.Role.JOURNAL_OWNER:
        has_access = (
            paper.publication.owner_id
            == user.id
        )

    elif user.role == User.Role.REVIEWER:
        from reviews.models import ReviewerAssignment

        has_access = (
            ReviewerAssignment.objects.filter(
                reviewer=user,
                review_round__paper_version=version,
            ).exists()
        )

    if not has_access:
        raise Http404(
            "Paper version not found."
        )

    version.file.open("rb")

    return FileResponse(
        version.file,
        content_type="application/pdf",
    )


@role_required([User.Role.AUTHOR])
def paper_submit(request):
    if request.method == "POST":
        form = PaperSubmissionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            with transaction.atomic():
                paper = form.save(
                    commit=False,
                )

                paper.corresponding_author = (
                    request.user
                )

                paper.status = (
                    Paper.Status.SUBMITTED
                )

                paper.submitted_at = (
                    timezone.now()
                )

                paper.save()

                PaperVersion.objects.create(
                    paper=paper,
                    version_number=1,
                    file=form.cleaned_data[
                        "paper_file"
                    ],
                    uploaded_by=request.user,
                )

            messages.success(
                request,
                (
                    "Research paper submitted "
                    "successfully."
                ),
            )

            return redirect(
                "author_dashboard",
            )

    else:
        form = PaperSubmissionForm()

    return render(
        request,
        "papers/paper_submit.html",
        {
            "form": form,
        },
    )


@role_required([User.Role.AUTHOR])
def my_submissions(request):
    papers = (
        Paper.objects.filter(
            corresponding_author=request.user,
        )
        .select_related(
            "publication",
        )
        .order_by(
            "-created_at",
        )
    )

    return render(
        request,
        "papers/my_submissions.html",
        {
            "papers": papers,
        },
    )


@role_required([User.Role.AUTHOR])
def paper_detail(request, pk):
    paper = get_object_or_404(
        Paper.objects.select_related(
            "publication",
            "final_decision",
            "copyediting",
        ).prefetch_related(
            "versions",
            "review_rounds__paper_version",
            (
                "review_rounds__"
                "reviewer_assignments"
            ),
        ),
        pk=pk,
        corresponding_author=request.user,
    )

    return render(
        request,
        "papers/paper_detail.html",
        {
            "paper": paper,
        },
    )


@role_required([User.Role.AUTHOR])
def paper_revision_upload(request, pk):
    from reviews.models import ReviewRound

    paper = get_object_or_404(
        Paper.objects.prefetch_related(
            "versions",
            "review_rounds",
        ),
        pk=pk,
        corresponding_author=request.user,
    )

    if (
        paper.status
        != Paper.Status.REVISION_REQUIRED
    ):
        messages.warning(
            request,
            (
                "A revised version can only "
                "be uploaded when revision "
                "is required."
            ),
        )

        return redirect(
            "paper_detail",
            pk=paper.pk,
        )

    if request.method == "POST":
        form = PaperRevisionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            with transaction.atomic():
                latest_version = (
                    paper.versions
                    .order_by(
                        "-version_number",
                    )
                    .first()
                )

                next_version_number = (
                    latest_version.version_number
                    + 1
                    if latest_version
                    else 1
                )

                new_version = (
                    PaperVersion.objects.create(
                        paper=paper,
                        version_number=(
                            next_version_number
                        ),
                        file=form.cleaned_data[
                            "paper_file"
                        ],
                        uploaded_by=request.user,
                    )
                )

                latest_round_number = (
                    paper.review_rounds
                    .order_by(
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

                ReviewRound.objects.create(
                    paper=paper,
                    paper_version=new_version,
                    round_number=(
                        next_round_number
                    ),
                    status=(
                        ReviewRound.Status.OPEN
                    ),
                )

                paper.status = (
                    Paper.Status.READY_FOR_REVIEW
                )

                paper.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            messages.success(
                request,
                (
                    f"Version "
                    f"{next_version_number} "
                    "uploaded successfully. "
                    f"Review Round "
                    f"{next_round_number} "
                    "is ready for Reviewer "
                    "assignment."
                ),
            )

            return redirect(
                "paper_detail",
                pk=paper.pk,
            )

    else:
        form = PaperRevisionForm()

    return render(
        request,
        "papers/paper_revision_upload.html",
        {
            "paper": paper,
            "form": form,
        },
    )


@role_required([User.Role.AUTHOR])
def copyediting_submission(request, pk):
    paper = get_object_or_404(
        Paper.objects.select_related(
            "copyediting",
        ).prefetch_related(
            "versions",
        ),
        pk=pk,
        corresponding_author=request.user,
    )

    if (
        paper.status
        != Paper.Status.COPYEDITING_CORRECTION_REQUIRED
        or paper.copyediting.status
        != Copyediting.Status.CORRECTION_REQUIRED
    ):
        messages.warning(
            request,
            (
                "A corrected copy can only "
                "be uploaded when copyediting "
                "corrections are required."
            ),
        )

        return redirect(
            "paper_detail",
            pk=paper.pk,
        )

    if request.method == "POST":
        form = CopyeditingSubmissionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            with transaction.atomic():
                latest_version = (
                    paper.versions
                    .order_by(
                        "-version_number",
                    )
                    .first()
                )

                next_version_number = (
                    latest_version.version_number
                    + 1
                    if latest_version
                    else 1
                )

                corrected_version = (
                    PaperVersion.objects.create(
                        paper=paper,
                        version_number=(
                            next_version_number
                        ),
                        file=form.cleaned_data[
                            "paper_file"
                        ],
                        uploaded_by=request.user,
                    )
                )

                copyediting = (
                    paper.copyediting
                )

                copyediting.corrected_version = (
                    corrected_version
                )

                copyediting.author_note = (
                    form.cleaned_data.get(
                        "author_note",
                        "",
                    )
                )

                copyediting.status = (
                    Copyediting.Status
                    .CORRECTION_SUBMITTED
                )

                copyediting.correction_submitted_at = (
                    timezone.now()
                )

                copyediting.save(
                    update_fields=[
                        "corrected_version",
                        "author_note",
                        "status",
                        (
                            "correction_"
                            "submitted_at"
                        ),
                    ]
                )

                paper.status = (
                    Paper.Status.COPYEDITING
                )

                paper.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            messages.success(
                request,
                (
                    f"Corrected Version "
                    f"{next_version_number} "
                    "submitted successfully "
                    "for copyediting review."
                ),
            )

            return redirect(
                "paper_detail",
                pk=paper.pk,
            )

    else:
        form = CopyeditingSubmissionForm()

    return render(
        request,
        "papers/copyediting_submission.html",
        {
            "paper": paper,
            "copyediting": paper.copyediting,
            "form": form,
        },
    )


@role_required([User.Role.EDITOR])
@require_POST
def start_copyediting(request, pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__editors=request.user,
        ).distinct(),
        pk=pk,
    )

    if (
        paper.status
        != Paper.Status.ACCEPTED
    ):
        messages.error(
            request,
            (
                "Copyediting can only be "
                "started for an accepted paper."
            ),
        )

        return redirect(
            "editor_paper_detail",
            pk=paper.pk,
        )

    with transaction.atomic():
        copyediting, created = (
            Copyediting.objects.get_or_create(
                paper=paper,
                defaults={
                    "started_by": request.user,
                },
            )
        )

        if not created:
            messages.info(
                request,
                (
                    "Copyediting has already "
                    "been started for this paper."
                ),
            )

            return redirect(
                "editor_paper_detail",
                pk=paper.pk,
            )

        paper.status = (
            Paper.Status.COPYEDITING
        )

        paper.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    messages.success(
        request,
        "Copyediting has been started.",
    )

    return redirect(
        "editor_paper_detail",
        pk=paper.pk,
    )


@role_required([User.Role.EDITOR])
def request_copyediting_correction(
    request,
    pk,
):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__editors=request.user,
        )
        .select_related(
            "copyediting",
        )
        .distinct(),
        pk=pk,
    )

    if (
        paper.status
        != Paper.Status.COPYEDITING
    ):
        messages.warning(
            request,
            (
                "Corrections can only be "
                "requested while copyediting "
                "is in progress."
            ),
        )

        return redirect(
            "editor_paper_detail",
            pk=paper.pk,
        )

    copyediting = paper.copyediting

    if request.method == "POST":
        form = CopyeditingCorrectionForm(
            request.POST,
        )

        if form.is_valid():
            with transaction.atomic():
                copyediting.status = (
                    Copyediting.Status
                    .CORRECTION_REQUIRED
                )

                copyediting.correction_note = (
                    form.cleaned_data[
                        "correction_note"
                    ]
                )

                copyediting.correction_requested_at = (
                    timezone.now()
                )

                copyediting.save(
                    update_fields=[
                        "status",
                        "correction_note",
                        (
                            "correction_"
                            "requested_at"
                        ),
                    ]
                )

                paper.status = (
                    Paper.Status
                    .COPYEDITING_CORRECTION_REQUIRED
                )

                paper.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            messages.success(
                request,
                (
                    "Copyediting corrections "
                    "have been requested from "
                    "the Author."
                ),
            )

            return redirect(
                "editor_paper_detail",
                pk=paper.pk,
            )

    else:
        form = CopyeditingCorrectionForm()

    return render(
        request,
        (
            "papers/"
            "copyediting_correction_request.html"
        ),
        {
            "paper": paper,
            "copyediting": copyediting,
            "form": form,
        },
    )


@role_required([User.Role.JOURNAL_OWNER])
def journal_owner_paper_detail(
    request,
    pk,
):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__owner=request.user,
        )
        .select_related(
            "publication",
            "corresponding_author",
            "final_decision",
            "production",
            "production__started_by",
            "production__published_by",
        )
        .prefetch_related(
            "versions",
            "review_rounds__paper_version",
            (
                "review_rounds__"
                "reviewer_assignments__reviewer"
            ),
        ),
        pk=pk,
    )

    return render(
        request,
        (
            "papers/"
            "journal_owner_paper_detail.html"
        ),
        {
            "paper": paper,
        },
    )


@role_required([User.Role.JOURNAL_OWNER])
@require_POST
def start_production(request, pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__owner=request.user,
        ),
        pk=pk,
    )

    if (
        paper.status
        != Paper.Status.READY_FOR_PRODUCTION
    ):
        messages.warning(
            request,
            (
                "Production can only be "
                "started when the paper is "
                "ready for production."
            ),
        )

        return redirect(
            "journal_owner_paper_detail",
            pk=paper.pk,
        )

    with transaction.atomic():
        production, created = (
            Production.objects.get_or_create(
                paper=paper,
                defaults={
                    "started_by": request.user,
                },
            )
        )

        if not created:
            messages.info(
                request,
                (
                    "Production has already "
                    "been started for this paper."
                ),
            )

            return redirect(
                "journal_owner_paper_detail",
                pk=paper.pk,
            )

        paper.status = (
            Paper.Status.IN_PRODUCTION
        )

        paper.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    messages.success(
        request,
        "Production has been started.",
    )

    return redirect(
        "journal_owner_paper_detail",
        pk=paper.pk,
    )


@role_required([User.Role.JOURNAL_OWNER])
@require_POST
def publish_paper(request, pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__owner=request.user,
        ).select_related(
            "production",
        ),
        pk=pk,
    )

    if (
        paper.status
        != Paper.Status.IN_PRODUCTION
        or paper.production.status
        != Production.Status.IN_PRODUCTION
    ):
        messages.warning(
            request,
            (
                "Only papers currently "
                "in production can be published."
            ),
        )

        return redirect(
            "journal_owner_paper_detail",
            pk=paper.pk,
        )

    with transaction.atomic():
        production = paper.production

        production.status = (
            Production.Status.PUBLISHED
        )

        production.published_by = (
            request.user
        )

        production.published_at = (
            timezone.now()
        )

        production.save(
            update_fields=[
                "status",
                "published_by",
                "published_at",
            ]
        )

        paper.status = (
            Paper.Status.PUBLISHED
        )

        paper.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    messages.success(
        request,
        (
            "Paper has been published "
            "successfully."
        ),
    )

    return redirect(
        "journal_owner_paper_detail",
        pk=paper.pk,
    )


@role_required([User.Role.EDITOR])
def editor_paper_list(request):
    papers = (
        Paper.objects.filter(
            publication__editors=request.user,
        )
        .select_related(
            "publication",
            "corresponding_author",
        )
        .order_by(
            "-submitted_at",
        )
        .distinct()
    )

    return render(
        request,
        "papers/editor_paper_list.html",
        {
            "papers": papers,
        },
    )


@role_required([User.Role.EDITOR])
def editor_review_workflow(request):
    review_statuses = [
        Paper.Status.READY_FOR_REVIEW,
        Paper.Status.UNDER_REVIEW,
        Paper.Status.REVISION_REQUIRED,
        Paper.Status.REVIEW_COMPLETED,
    ]

    papers = (
        Paper.objects.filter(
            publication__editors=request.user,
            status__in=review_statuses,
        )
        .select_related(
            "publication",
            "corresponding_author",
        )
        .prefetch_related(
            "review_rounds__paper_version",
            (
                "review_rounds__"
                "reviewer_assignments__reviewer"
            ),
        )
        .order_by(
            "-submitted_at",
        )
        .distinct()
    )

    return render(
        request,
        "papers/editor_review_workflow.html",
        {
            "papers": papers,
        },
    )


@role_required([User.Role.EDITOR])
def editor_paper_detail(request, pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__editors=request.user,
        )
        .select_related(
            "publication",
            "corresponding_author",
            "final_decision",
            "copyediting",
            "copyediting__corrected_version",
        )
        .prefetch_related(
            "versions",
            "review_rounds__paper_version",
            (
                "review_rounds__"
                "reviewer_assignments__reviewer"
            ),
        ),
        pk=pk,
    )

    return render(
        request,
        "papers/editor_paper_detail.html",
        {
            "paper": paper,
        },
    )


@role_required([User.Role.EDITOR])
@require_POST
def complete_copyediting(request, pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__editors=request.user,
        )
        .select_related(
            "copyediting",
            "copyediting__corrected_version",
        )
        .distinct(),
        pk=pk,
    )

    if paper.status != Paper.Status.COPYEDITING:
        messages.warning(
            request,
            (
                "Copyediting can only be completed "
                "while copyediting is in progress."
            ),
        )

        return redirect(
            "editor_paper_detail",
            pk=paper.pk,
        )

    allowed_copyediting_statuses = [
        Copyediting.Status.IN_PROGRESS,
        Copyediting.Status.CORRECTION_SUBMITTED,
    ]

    if (
        paper.copyediting.status
        not in allowed_copyediting_statuses
    ):
        messages.warning(
            request,
            (
                "Copyediting cannot be completed "
                "until the required Author correction "
                "has been submitted."
            ),
        )

        return redirect(
            "editor_paper_detail",
            pk=paper.pk,
        )

    if (
        paper.copyediting.status
        == Copyediting.Status.CORRECTION_SUBMITTED
        and not paper.copyediting.corrected_version
    ):
        messages.error(
            request,
            (
                "No corrected paper version "
                "was found."
            ),
        )

        return redirect(
            "editor_paper_detail",
            pk=paper.pk,
        )

    with transaction.atomic():
        copyediting = paper.copyediting

        copyediting.status = (
            Copyediting.Status.COMPLETED
        )

        copyediting.completed_by = (
            request.user
        )

        copyediting.completed_at = (
            timezone.now()
        )

        copyediting.save(
            update_fields=[
                "status",
                "completed_by",
                "completed_at",
            ]
        )

        paper.status = (
            Paper.Status.READY_FOR_PRODUCTION
        )

        paper.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    messages.success(
        request,
        (
            "Copyediting has been completed. "
            "The paper is ready for production."
        ),
    )

    return redirect(
        "editor_paper_detail",
        pk=paper.pk,
    )


@role_required([User.Role.EDITOR])
def editor_paper_screening(request, pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__editors=request.user,
        ),
        pk=pk,
    )

    allowed_statuses = [
        Paper.Status.SUBMITTED,
        Paper.Status.UNDER_INITIAL_REVIEW,
    ]

    if paper.status not in allowed_statuses:
        messages.warning(
            request,
            (
                "Initial screening is no longer "
                "available for this paper."
            ),
        )

        return redirect(
            "editor_paper_detail",
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
                "editor_paper_detail",
                pk=paper.pk,
            )

    else:
        form = InitialScreeningForm(
            instance=paper,
        )

    return render(
        request,
        "papers/editor_paper_screening.html",
        {
            "form": form,
            "paper": paper,
        },
    )


@role_required([User.Role.EDITOR])
def paper_final_decision(request, pk):
    paper = get_object_or_404(
        Paper.objects.filter(
            publication__editors=request.user,
        ),
        pk=pk,
    )

    if (
        paper.status
        != Paper.Status.REVIEW_COMPLETED
    ):
        messages.warning(
            request,
            (
                "The review must be completed "
                "before making the final decision."
            ),
        )

        return redirect(
            "editor_paper_detail",
            pk=paper.pk,
        )

    if request.method == "POST":
        form = FinalDecisionForm(
            request.POST,
            instance=paper,
        )

        if form.is_valid():
            with transaction.atomic():
                paper = form.save()

                FinalDecision.objects.update_or_create(
                    paper=paper,
                    defaults={
                        "decision": paper.status,
                        "decided_by": request.user,
                        "note": (
                            form.cleaned_data.get(
                                "note",
                                "",
                            )
                        ),
                    },
                )

            messages.success(
                request,
                (
                    f"Paper has been "
                    f"{paper.get_status_display().lower()}."
                ),
            )

            return redirect(
                "editor_paper_detail",
                pk=paper.pk,
            )

    else:
        form = FinalDecisionForm(
            instance=paper,
        )

    return render(
        request,
        "papers/paper_final_decision.html",
        {
            "form": form,
            "paper": paper,
        },
    )