# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2020 Dimpact
from unittest import skip

from django.contrib.sites.models import Site
from django.test import override_settings

from django_db_logger.models import StatusLog
from freezegun import freeze_time
from rest_framework import status
from vng_api_common.tests import reverse

from openzaak.components.catalogi.tests.factories import (
    ZaakTypeInformatieObjectTypeFactory,
)
from openzaak.components.documenten.tests.factories import (
    EnkelvoudigInformatieObjectFactory,
)
from openzaak.notifications.models import FailedNotification
from openzaak.notifications.tests.mixins import NotificationsConfigMixin
from openzaak.tests.utils import APICMISTestCase, JWTAuthMixin, require_cmis

from .factories import ZaakFactory, ZaakInformatieObjectFactory
from .utils import get_operation_url

VERANTWOORDELIJKE_ORGANISATIE = "517439943"


@require_cmis
@override_settings(NOTIFICATIONS_DISABLED=False, CMIS_ENABLED=True)
@freeze_time("2019-01-01T12:00:00Z")
class FailedNotificationCMISTests(
    NotificationsConfigMixin, JWTAuthMixin, APICMISTestCase
):
    heeft_alle_autorisaties = True
    maxDiff = None

    def test_zaakinformatieobject_create_fail_send_notification_create_db_entry(self):
        site = Site.objects.get_current()
        url = get_operation_url("zaakinformatieobject_create")

        zaak = ZaakFactory.create()
        zaak_url = reverse(zaak)
        io = EnkelvoudigInformatieObjectFactory.create(
            informatieobjecttype__concept=False
        )
        io_url = f"http://testserver{reverse(io)}"
        ZaakTypeInformatieObjectTypeFactory.create(
            zaaktype=zaak.zaaktype, informatieobjecttype=io.informatieobjecttype
        )

        data = {
            "informatieobject": io_url,
            "zaak": f"http://{site.domain}{zaak_url}",
        }

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        data = response.json()

        self.assertEqual(StatusLog.objects.count(), 1)

        logged_warning = StatusLog.objects.get()
        failed = FailedNotification.objects.get()
        message = {
            "aanmaakdatum": "2019-01-01T12:00:00Z",
            "actie": "create",
            "hoofdObject": f"http://testserver{zaak_url}",
            "kanaal": "zaken",
            "kenmerken": {
                "bronorganisatie": zaak.bronorganisatie,
                "zaaktype": f"http://testserver{reverse(zaak.zaaktype)}",
                "vertrouwelijkheidaanduiding": zaak.vertrouwelijkheidaanduiding,
            },
            "resource": "zaakinformatieobject",
            "resourceUrl": data["url"],
        }

        self.assertEqual(failed.statuslog_ptr, logged_warning)
        self.assertEqual(failed.message, message)

    @skip(reason="Standard does not prescribe ZIO destroy notifications.")
    def test_zaakinformatieobject_delete_fail_send_notification_create_db_entry(self):
        io = EnkelvoudigInformatieObjectFactory.create()
        io_url = f"http://testserver{reverse(io)}"

        zio = ZaakInformatieObjectFactory.create(informatieobject=io_url)
        url = reverse(zio)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(StatusLog.objects.count(), 1)

        logged_warning = StatusLog.objects.get()
        failed = FailedNotification.objects.get()
        message = {
            "aanmaakdatum": "2019-01-01T12:00:00Z",
            "actie": "destroy",
            "hoofdObject": f"http://testserver{reverse(zio.zaak)}",
            "kanaal": "zaken",
            "kenmerken": {
                "bronorganisatie": zio.zaak.bronorganisatie,
                "zaaktype": f"http://testserver{reverse(zio.zaak.zaaktype)}",
                "vertrouwelijkheidaanduiding": zio.zaak.vertrouwelijkheidaanduiding,
            },
            "resource": "zaakinformatieobject",
            "resourceUrl": f"http://testserver{url}",
        }

        self.assertEqual(failed.statuslog_ptr, logged_warning)
        self.assertEqual(failed.message, message)
