# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2022 Dimpact
# Generated by Django 3.2.15 on 2022-09-01 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documenten", "0013_alter_bestandsdeel_datetime_created"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="bestandsdeel",
            options={
                "verbose_name": "bestandsdeel",
                "verbose_name_plural": "bestandsdelen",
            },
        ),
        migrations.AlterUniqueTogether(
            name="bestandsdeel",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="bestandsdeel",
            constraint=models.UniqueConstraint(
                condition=models.Q(("informatieobject__isnull", False)),
                fields=("informatieobject", "volgnummer"),
                name="unique_informatieobject_fk_and_volgnummer",
            ),
        ),
        migrations.AddConstraint(
            model_name="bestandsdeel",
            constraint=models.UniqueConstraint(
                condition=models.Q(("informatieobject_uuid__isnull", False)),
                fields=("informatieobject_uuid", "volgnummer"),
                name="unique_informatieobject_uuid_and_volgnummer",
            ),
        ),
        migrations.AddConstraint(
            model_name="bestandsdeel",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("informatieobject__isnull", True),
                        ("informatieobject_uuid__isnull", False),
                    ),
                    models.Q(
                        ("informatieobject__isnull", False),
                        ("informatieobject_uuid__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="informatieobject_fk_or_informatieobject_mutex",
            ),
        ),
    ]
