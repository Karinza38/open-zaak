# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2021 Dimpact
# Generated by Django 2.2.25 on 2021-12-22 09:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0011_migrate_to_zgw_consumers_nlx"),
    ]

    operations = [
        migrations.DeleteModel(
            name="NLXConfig",
        ),
    ]
