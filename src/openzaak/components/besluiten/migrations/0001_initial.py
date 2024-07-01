# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2019 - 2020 Dimpact
# Generated by Django 2.2.9 on 2020-01-24 10:05

from django.db import migrations, models
import django_loose_fk.fields
import openzaak.utils.mixins
import uuid
import vng_api_common.fields
import vng_api_common.models
import vng_api_common.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Besluit",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        help_text="Unieke resource identifier (UUID4)",
                        unique=True,
                    ),
                ),
                (
                    "identificatie",
                    models.CharField(
                        blank=True,
                        help_text="Identificatie van het besluit binnen de organisatie die het besluit heeft vastgesteld. Indien deze niet opgegeven is, dan wordt die gegenereerd.",
                        max_length=50,
                        validators=[
                            vng_api_common.validators.AlphanumericExcludingDiacritic()
                        ],
                        verbose_name="identificatie",
                    ),
                ),
                (
                    "verantwoordelijke_organisatie",
                    vng_api_common.fields.RSINField(
                        db_index=True,
                        help_text="Het RSIN van de niet-natuurlijk persoon zijnde de organisatie die het besluit heeft vastgesteld.",
                        max_length=9,
                        verbose_name="verantwoordelijke organisatie",
                    ),
                ),
                (
                    "_besluittype_url",
                    models.URLField(
                        blank=True,
                        help_text="URL-referentie naar extern BESLUITTYPE (in een andere Catalogi API).",
                        max_length=1000,
                        verbose_name="extern besluittype",
                    ),
                ),
                (
                    "_zaak_url",
                    models.URLField(
                        blank=True,
                        help_text="URL-referentie naar de ZAAK (in de Zaken API) waarvan dit besluit uitkomst is.",
                        max_length=1000,
                        verbose_name="externe zaak",
                    ),
                ),
                (
                    "datum",
                    models.DateField(
                        help_text="De beslisdatum (AWB) van het besluit.",
                        validators=[vng_api_common.validators.UntilTodayValidator()],
                        verbose_name="datum",
                    ),
                ),
                (
                    "toelichting",
                    models.TextField(
                        blank=True,
                        help_text="Toelichting bij het besluit.",
                        verbose_name="toelichting",
                    ),
                ),
                (
                    "bestuursorgaan",
                    models.CharField(
                        blank=True,
                        help_text="Een orgaan van een rechtspersoon krachtens publiekrecht ingesteld of een persoon of college, met enig openbaar gezag bekleed onder wiens verantwoordelijkheid het besluit vastgesteld is.",
                        max_length=50,
                        verbose_name="bestuursorgaan",
                    ),
                ),
                (
                    "ingangsdatum",
                    models.DateField(
                        help_text="Ingangsdatum van de werkingsperiode van het besluit.",
                        verbose_name="ingangsdatum",
                    ),
                ),
                (
                    "vervaldatum",
                    models.DateField(
                        blank=True,
                        help_text="Datum waarop de werkingsperiode van het besluit eindigt.",
                        null=True,
                        verbose_name="vervaldatum",
                    ),
                ),
                (
                    "vervalreden",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("tijdelijk", "Besluit met tijdelijke werking"),
                            (
                                "ingetrokken_overheid",
                                "Besluit ingetrokken door overheid",
                            ),
                            (
                                "ingetrokken_belanghebbende",
                                "Besluit ingetrokken o.v.v. belanghebbende",
                            ),
                        ],
                        help_text="De omschrijving die aangeeft op grond waarvan het besluit is of komt te vervallen.",
                        max_length=30,
                        verbose_name="vervalreden",
                    ),
                ),
                (
                    "publicatiedatum",
                    models.DateField(
                        blank=True,
                        help_text="Datum waarop het besluit gepubliceerd wordt.",
                        null=True,
                        verbose_name="publicatiedatum",
                    ),
                ),
                (
                    "verzenddatum",
                    models.DateField(
                        blank=True,
                        help_text="Datum waarop het besluit verzonden is.",
                        null=True,
                        verbose_name="verzenddatum",
                    ),
                ),
                (
                    "uiterlijke_reactiedatum",
                    models.DateField(
                        blank=True,
                        help_text="De datum tot wanneer verweer tegen het besluit mogelijk is.",
                        null=True,
                        verbose_name="uiterlijke reactiedatum",
                    ),
                ),
                (
                    "_zaakbesluit_url",
                    models.URLField(
                        blank=True,
                        help_text="URL of related ZaakBesluit object in the other API",
                        max_length=1000,
                    ),
                ),
            ],
            options={
                "verbose_name": "besluit",
                "verbose_name_plural": "besluiten",
            },
            bases=(
                openzaak.utils.mixins.AuditTrailMixin,
                vng_api_common.models.APIMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="BesluitInformatieObject",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        help_text="Unieke resource identifier (UUID4)",
                        unique=True,
                    ),
                ),
                (
                    "_informatieobject_url",
                    models.URLField(
                        blank=True,
                        help_text="URL to the informatieobject in an external API",
                        max_length=1000,
                        verbose_name="External informatieobject",
                    ),
                ),
                (
                    "_objectinformatieobject_url",
                    models.URLField(
                        blank=True,
                        help_text="URL of related ObjectInformatieObject object in the other API",
                        max_length=1000,
                    ),
                ),
            ],
            options={
                "verbose_name": "besluitinformatieobject",
                "verbose_name_plural": "besluitinformatieobjecten",
            },
        ),
    ]
