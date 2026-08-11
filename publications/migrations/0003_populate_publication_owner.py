from django.db import migrations


def populate_publication_owner(apps, schema_editor):
    Publication = apps.get_model(
        "publications",
        "Publication",
    )
    User = apps.get_model(
        "accounts",
        "User",
    )

    fallback_owner = (
        User.objects.filter(
            role="JOURNAL_OWNER",
            is_superuser=True,
        ).first()
        or User.objects.filter(
            role="JOURNAL_OWNER",
        ).first()
    )

    publications = Publication.objects.filter(
        owner__isnull=True,
    )

    for publication in publications:
        created_by = publication.created_by

        if (
            created_by
            and created_by.role == "JOURNAL_OWNER"
        ):
            publication.owner = created_by

        elif fallback_owner:
            publication.owner = fallback_owner

        else:
            raise RuntimeError(
                "Cannot assign publication owner because "
                "no Journal Owner account exists."
            )

        publication.save(
            update_fields=["owner"],
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "publications",
            "0002_publication_editors_publication_owner",
        ),
    ]

    operations = [
        migrations.RunPython(
            populate_publication_owner,
            migrations.RunPython.noop,
        ),
    ]