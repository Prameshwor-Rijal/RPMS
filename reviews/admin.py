from django.contrib import admin

from .models import ReviewerAssignment


@admin.register(ReviewerAssignment)
class ReviewerAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "paper",
        "reviewer",
        "status",
        "assigned_by",
        "assigned_at",
    )

    list_filter = (
        "status",
        "assigned_at",
    )

    search_fields = (
        "paper__title",
        "reviewer__username",
        "reviewer__email",
    )

    readonly_fields = (
        "assigned_at",
        "responded_at",
        "completed_at",
    )

    list_select_related = (
        "paper",
        "reviewer",
        "assigned_by",
    )