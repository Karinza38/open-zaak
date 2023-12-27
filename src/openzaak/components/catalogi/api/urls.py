# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2019 - 2020 Dimpact
from django.conf.urls import url
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from vng_api_common import routers

from ..api.schema import custom_settings
from .viewsets import (
    BesluitTypeViewSet,
    CatalogusViewSet,
    EigenschapViewSet,
    InformatieObjectTypeViewSet,
    ResultaatTypeViewSet,
    RolTypeViewSet,
    StatusTypeViewSet,
    ZaakObjectTypeViewSet,
    ZaakTypeInformatieObjectTypeViewSet,
    ZaakTypeViewSet,
)

router = routers.DefaultRouter()
router.register(r"catalogussen", CatalogusViewSet)
router.register(r"zaaktypen", ZaakTypeViewSet)
router.register(r"statustypen", StatusTypeViewSet)
router.register(r"eigenschappen", EigenschapViewSet)
router.register(r"roltypen", RolTypeViewSet)
router.register(r"informatieobjecttypen", InformatieObjectTypeViewSet)
router.register(r"besluittypen", BesluitTypeViewSet)
router.register(r"resultaattypen", ResultaatTypeViewSet)
router.register(r"zaaktype-informatieobjecttypen", ZaakTypeInformatieObjectTypeViewSet)
router.register(r"zaakobjecttypen", ZaakObjectTypeViewSet)


urlpatterns = [
    url(
        r"^v(?P<version>\d+)/",
        include(
            [
                # API documentation
                path(
                    "schema/openapi.yaml",
                    SpectacularAPIView.as_view(
                        urlconf="openzaak.components.catalogi.api.urls",
                        custom_settings=custom_settings,
                    ),
                    name="schema-catalogi",
                ),
                path(
                    "schema/",
                    SpectacularRedocView.as_view(url_name="schema-catalogi"),
                    name="schema-catalogi-redoc",
                ),
                # actual API
                url(r"^", include(router.urls)),
                # should not be picked up by drf-yasg
                path("", router.APIRootView.as_view(), name="api-root-catalogi"),
                path("", include("vng_api_common.notifications.api.urls")),
            ]
        ),
    )
]
