from django.contrib import admin

from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "publication_type",
        "status",
        "submission_deadline",
        "review_deadline",
        "created_by",
    )

    list_filter = (
        "publication_type",
        "status",
    )

    search_fields = (
        "name",
        "location",
    )

    readonly_fields = (
        "created_by",
        "created_at",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)
