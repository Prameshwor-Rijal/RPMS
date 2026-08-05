from django.contrib import admin

from .models import Paper, PaperVersion


class PaperVersionInline(admin.TabularInline):
    model = PaperVersion
    extra = 0
    readonly_fields = ("uploaded_at",)
    show_change_link = True


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "publication",
        "corresponding_author",
        "status",
        "submitted_at",
    )

    list_filter = (
        "status",
        "publication",
        "research_category",
    )

    search_fields = (
        "title",
        "keywords",
        "corresponding_author__username",
        "corresponding_author__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [
        PaperVersionInline,
    ]


@admin.register(PaperVersion)
class PaperVersionAdmin(admin.ModelAdmin):
    list_display = (
        "paper",
        "version_number",
        "uploaded_by",
        "uploaded_at",
    )

    search_fields = (
        "paper__title",
        "uploaded_by__username",
        "uploaded_by__email",
    )

    readonly_fields = ("uploaded_at",)
