from django.shortcuts import get_object_or_404, redirect, render

from django.utils import timezone
from accounts.models import User
from dashboard.decorators import role_required

from .forms import PublicationForm
from .models import Publication


@role_required([User.Role.ADMIN])
def publication_list(request):
    publications = Publication.objects.all()

    return render(
        request,
        "publications/publication_list.html",
        {"publications": publications},
    )


@role_required([User.Role.AUTHOR])
def available_publications(request):
    today = timezone.localdate()

    publications = Publication.objects.filter(
        status=Publication.Status.OPEN,
        submission_open_date__lte=today,
        submission_deadline__gte=today,
    ).order_by("submission_deadline")

    return render(
        request,
        "publications/available_publications.html",
        {"publications": publications},
    )


@role_required([User.Role.ADMIN])
def publication_detail(request, pk):
    publication = get_object_or_404(Publication, pk=pk)

    return render(
        request,
        "publications/publication_detail.html",
        {"publication": publication},
    )


@role_required([User.Role.ADMIN])
def publication_update(request, pk):
    publication = get_object_or_404(Publication, pk=pk)

    if request.method == "POST":
        form = PublicationForm(
            request.POST,
            instance=publication,
        )

        if form.is_valid():
            form.save()
            return redirect(
                "publication_detail",
                pk=publication.pk,
            )
    else:
        form = PublicationForm(instance=publication)

    return render(
        request,
        "publications/publication_update.html",
        {
            "form": form,
            "publication": publication,
        },
    )


@role_required([User.Role.ADMIN])
def publication_delete(request, pk):
    publication = get_object_or_404(Publication, pk=pk)

    if request.method == "POST":
        publication.delete()
        return redirect("publication_list")

    return render(
        request,
        "publications/publication_confirm_delete.html",
        {"publication": publication},
    )


@role_required([User.Role.ADMIN])
def publication_create(request):
    if request.method == "POST":
        form = PublicationForm(request.POST)

        if form.is_valid():
            publication = form.save(commit=False)
            publication.created_by = request.user
            publication.save()

            return redirect("publication_list")
    else:
        form = PublicationForm()

    return render(
        request,
        "publications/publication_form.html",
        {"form": form},
    )
