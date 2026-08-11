from django.contrib import admin

from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "publication_type",
        "lifecycle_status",
        "submission_status_display_admin",
        "submission_deadline",
        "review_deadline",
        "owner",
        "created_by",
    )

    list_filter = (
        "publication_type",
        "lifecycle_status",
        "owner",
    )

    search_fields = (
        "name",
        "location",
        "owner__username",
    )

    readonly_fields = (
        "created_by",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Submission Status")
    def submission_status_display_admin(self, obj):
        return obj.submission_status_display

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )