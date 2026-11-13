from django.db import migrations


def populate_review_rounds(apps, schema_editor):
    PaperVersion = apps.get_model("papers", "PaperVersion")
    ReviewRound = apps.get_model("reviews", "ReviewRound")
    ReviewerAssignment = apps.get_model(
        "reviews",
        "ReviewerAssignment",
    )

    paper_ids = (
        ReviewerAssignment.objects
        .filter(review_round__isnull=True)
        .order_by()
        .values_list("paper_id", flat=True)
        .distinct()
    )

    for paper_id in paper_ids:
        paper_version = (
            PaperVersion.objects
            .filter(
                paper_id=paper_id,
                version_number=1,
            )
            .first()
        )

        if paper_version is None:
            raise RuntimeError(
                f"Paper {paper_id} does not have Version 1."
            )

        paper = paper_version.paper

        if paper.status == "REVISION_REQUIRED":
            round_status = "REVISION_REQUIRED"

        elif paper.status in (
            "REVIEW_COMPLETED",
            "ACCEPTED",
            "REJECTED",
        ):
            round_status = "COMPLETED"

        else:
            round_status = "OPEN"

        review_round = ReviewRound.objects.create(
            paper_id=paper_id,
            paper_version_id=paper_version.id,
            round_number=1,
            status=round_status,
        )

        ReviewerAssignment.objects.filter(
            paper_id=paper_id,
            review_round__isnull=True,
        ).update(
            review_round_id=review_round.id
        )


class Migration(migrations.Migration):

    dependencies = [
        ("reviews", "0005_reviewerassignment_review_round"),
    ]

    operations = [
        migrations.RunPython(
            populate_review_rounds,
            migrations.RunPython.noop,
        ),
    ]