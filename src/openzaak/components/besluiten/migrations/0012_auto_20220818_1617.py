# Generated by Django 3.2.14 on 2022-08-18 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("besluiten", "0011_auto_20220815_1739"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="besluit", name="_besluittype_or__besluittype_base_url_filled",
        ),
        migrations.RemoveConstraint(
            model_name="besluitinformatieobject",
            name="_informatieobject_or__informatieobject_base_url_filled",
        ),
        migrations.AddConstraint(
            model_name="besluit",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(("_besluittype__isnull", True), _negated=True),
                        ("_besluittype_base_url__isnull", True),
                    ),
                    models.Q(
                        ("_besluittype__isnull", True),
                        models.Q(
                            ("_besluittype_base_url__isnull", True), _negated=True
                        ),
                    ),
                    _connector="OR",
                ),
                name="besluiten_besluit__besluittype_or__besluittype_base_url_filled",
            ),
        ),
        migrations.AddConstraint(
            model_name="besluitinformatieobject",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(("_informatieobject__isnull", True), _negated=True),
                        ("_informatieobject_base_url__isnull", True),
                    ),
                    models.Q(
                        ("_informatieobject__isnull", True),
                        models.Q(
                            ("_informatieobject_base_url__isnull", True), _negated=True
                        ),
                    ),
                    _connector="OR",
                ),
                name="besluiten_besluitinformatieobject__informatieobject_or__informatieobject_base_url_filled",
            ),
        ),
    ]
