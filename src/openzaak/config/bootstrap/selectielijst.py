# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2024 Dimpact
from django.conf import settings

import requests
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from zds_client import ClientError
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openzaak.selectielijst.api import get_procestypen
from openzaak.selectielijst.models import ReferentieLijstConfig


class SelectielijstAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the Open Zaak client to request Selectielijst API

    1. Create service for Selectielijst API
    2. Set up configuration for Selectielijst API client

    Normal mode doesn't change the allowed and default years
    If they are changed, run this command with 'overwrite' flag
    """

    verbose_name = "Selectielijst API Configuration"
    enable_setting = "OPENZAAK_SELECTIELIJST_CONFIG_ENABLE"

    def is_configured(self) -> bool:
        service = Service.objects.filter(api_root=settings.SELECTIELIJST_API_ROOT)
        selectielijst_config = ReferentieLijstConfig.get_solo()

        return service.exists() and bool(
            selectielijst_config.api_root == settings.SELECTIELIJST_API_ROOT
        )

    def configure(self):
        # 1. Set up a service for the Selectielijst API so Open Zaak can request it
        Service.objects.update_or_create(
            api_root=settings.SELECTIELIJST_API_ROOT,
            defaults={
                "label": "Selectielijst API",
                "api_type": APITypes.orc,
                "oas": settings.SELECTIELIJST_API_OAS,
                "auth_type": AuthTypes.no_auth,
            },
        )

        # 2. Set up configuration
        config = ReferentieLijstConfig.get_solo()
        if config.api_root != settings.SELECTIELIJST_API_ROOT:
            config.api_root = settings.SELECTIELIJST_API_ROOT
            config.allowed_years = settings.SELECTIELIJST_ALLOWED_YEARS
            config.default_year = settings.SELECTIELIJST_DEFAULT_YEAR
            config.save(update_fields=["api_root", "allowed_years", "default_year"])

    def test_configuration(self):
        """
        fetch procestypen
        """
        # check if we can fetch list of kanalen
        try:
            get_procestypen()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve procestypen from Selectielijst API."
            ) from exc
