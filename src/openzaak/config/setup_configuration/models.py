# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2024 Dimpact
from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from pydantic import PositiveInt

from openzaak.selectielijst.models import ReferentieLijstConfig


class SelectielijstAPIConfig(ConfigurationModel):

    allowed_years: list[PositiveInt] = DjangoModelRef(
        ReferentieLijstConfig, "allowed_years"
    )

    selectielijst_api_service_identifier: str = DjangoModelRef(
        ReferentieLijstConfig,
        "service",
    )

    class Meta:
        django_model_refs = {
            ReferentieLijstConfig: [
                "default_year",
            ],
        }
