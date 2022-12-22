# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2019 - 2020 Dimpact
import base64
import uuid
from unittest.mock import patch

from django.test import override_settings, tag

import requests_mock
from django_db_logger.models import StatusLog
from freezegun import freeze_time
from notifications_api_common.tests.utils import mock_notify
from notifications_api_common.viewsets import NotificationException
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.constants import VertrouwelijkheidsAanduiding
from vng_api_common.tests import reverse

from openzaak.components.catalogi.tests.factories import InformatieObjectTypeFactory
from openzaak.components.documenten.models import EnkelvoudigInformatieObject
from openzaak.notifications.models import FailedNotification
from openzaak.notifications.tests import mock_notification_send, mock_nrc_oas_get
from openzaak.notifications.tests.mixins import NotificationsConfigMixin
from openzaak.notifications.tests.utils import LOGGING_SETTINGS
from openzaak.tests.utils import JWTAuthMixin

from .factories import EnkelvoudigInformatieObjectFactory, GebruiksrechtenFactory
from .utils import get_operation_url


@tag("notifications")
@requests_mock.Mocker()
@freeze_time("2012-01-14")
@override_settings(NOTIFICATIONS_DISABLED=False)
@patch(
    "notifications_api_common.viewsets.NotificationViewSetMixin.send_notification.delay",
    side_effect=mock_notify,
)
class SendNotifTestCase(NotificationsConfigMixin, JWTAuthMixin, APITestCase):

    heeft_alle_autorisaties = True

    @patch("zds_client.Client.from_url")
    def test_send_notif_create_enkelvoudiginformatieobject(
        self, m, mock_client, mock_notif
    ):
        """
        Registreer een ENKELVOUDIGINFORMATIEOBJECT
        """
        mock_nrc_oas_get(m)
        informatieobjecttype = InformatieObjectTypeFactory.create(concept=False)
        informatieobjecttype_url = reverse(informatieobjecttype)
        client = mock_client.return_value
        url = get_operation_url("enkelvoudiginformatieobject_create")
        data = {
            "identificatie": "AMS20180701001",
            "bronorganisatie": "159351741",
            "creatiedatum": "2018-07-01",
            "titel": "text_extra.txt",
            "auteur": "ANONIEM",
            "formaat": "text/plain",
            "taal": "dut",
            "inhoud": base64.b64encode(b"Extra tekst in bijlage").decode("utf-8"),
            "informatieobjecttype": f"http://testserver{informatieobjecttype_url}",
            "vertrouwelijkheidaanduiding": VertrouwelijkheidsAanduiding.openbaar,
        }

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        data = response.json()
        client.create.assert_called_once_with(
            "notificaties",
            {
                "kanaal": "documenten",
                "hoofdObject": data["url"],
                "resource": "enkelvoudiginformatieobject",
                "resourceUrl": data["url"],
                "actie": "create",
                "aanmaakdatum": "2012-01-14T00:00:00Z",
                "kenmerken": {
                    "bronorganisatie": "159351741",
                    "informatieobjecttype": f"http://testserver{informatieobjecttype_url}",
                    "vertrouwelijkheidaanduiding": VertrouwelijkheidsAanduiding.openbaar,
                },
            },
        )


@tag("notifications")
@requests_mock.Mocker()
@override_settings(NOTIFICATIONS_DISABLED=False, LOGGING=LOGGING_SETTINGS)
@freeze_time("2019-01-01T12:00:00Z")
@patch(
    "notifications_api_common.viewsets.NotificationViewSetMixin.send_notification.delay",
    side_effect=mock_notify,
)
class FailedNotificationTests(NotificationsConfigMixin, JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True
    maxDiff = None

    def test_eio_create_fail_send_notification_create_db_entry(self, m, mock_notif):
        mock_nrc_oas_get(m)
        mock_notification_send(m, status_code=403)
        url = get_operation_url("enkelvoudiginformatieobject_create")

        informatieobjecttype = InformatieObjectTypeFactory.create(concept=False)
        informatieobjecttype_url = reverse(informatieobjecttype)
        data = {
            "identificatie": uuid.uuid4().hex,
            "bronorganisatie": "159351741",
            "creatiedatum": "2018-06-27",
            "titel": "detailed summary",
            "auteur": "test_auteur",
            "formaat": "txt",
            "taal": "eng",
            "bestandsnaam": "dummy.txt",
            "inhoud": base64.b64encode(b"some file content").decode("utf-8"),
            "link": "http://een.link",
            "beschrijving": "test_beschrijving",
            "informatieobjecttype": f"http://testserver{informatieobjecttype_url}",
            "vertrouwelijkheidaanduiding": "openbaar",
        }

        with self.assertRaises(NotificationException):
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
            "hoofdObject": data["url"],
            "kanaal": "documenten",
            "kenmerken": {
                "bronorganisatie": "159351741",
                "informatieobjecttype": f"http://testserver{informatieobjecttype_url}",
                "vertrouwelijkheidaanduiding": "openbaar",
            },
            "resource": "enkelvoudiginformatieobject",
            "resourceUrl": data["url"],
        }

        self.assertEqual(failed.statuslog_ptr, logged_warning)
        self.assertEqual(failed.message, message)

    def test_eio_delete_fail_send_notification_create_db_entry(self, m, mock_notif):
        mock_nrc_oas_get(m)
        mock_notification_send(m, status_code=403)
        eio = EnkelvoudigInformatieObjectFactory.create()
        url = reverse(eio)

        with self.assertRaises(NotificationException):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(StatusLog.objects.count(), 1)

        logged_warning = StatusLog.objects.get()
        failed = FailedNotification.objects.get()
        message = {
            "aanmaakdatum": "2019-01-01T12:00:00Z",
            "actie": "destroy",
            "hoofdObject": f"http://testserver{url}",
            "kanaal": "documenten",
            "kenmerken": {
                "bronorganisatie": eio.bronorganisatie,
                "informatieobjecttype": f"http://testserver{reverse(eio.informatieobjecttype)}",
                "vertrouwelijkheidaanduiding": eio.vertrouwelijkheidaanduiding,
            },
            "resource": "enkelvoudiginformatieobject",
            "resourceUrl": f"http://testserver{url}",
        }

        self.assertEqual(failed.statuslog_ptr, logged_warning)
        self.assertEqual(failed.message, message)

    def test_gebruiksrechten_create_fail_send_notification_create_db_entry(
        self, m, mock_notif
    ):
        mock_nrc_oas_get(m)
        mock_notification_send(m, status_code=403)
        url = get_operation_url("gebruiksrechten_create")

        eio = EnkelvoudigInformatieObjectFactory.create()
        eio_url = reverse(eio)
        data = {
            "informatieobject": f"http://testserver{eio_url}",
            "startdatum": "2018-12-24T00:00:00Z",
            "omschrijvingVoorwaarden": "Een hele set onredelijke voorwaarden",
        }

        with self.assertRaises(NotificationException):
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
            "hoofdObject": f"http://testserver{eio_url}",
            "kanaal": "documenten",
            "kenmerken": {
                "bronorganisatie": eio.bronorganisatie,
                "informatieobjecttype": f"http://testserver{reverse(eio.informatieobjecttype)}",
                "vertrouwelijkheidaanduiding": eio.vertrouwelijkheidaanduiding,
            },
            "resource": "gebruiksrechten",
            "resourceUrl": data["url"],
        }

        self.assertEqual(failed.statuslog_ptr, logged_warning)
        self.assertEqual(failed.message, message)

    def test_gebruiksrechten_delete_fail_send_notification_create_db_entry(
        self, m, mock_notif
    ):
        mock_nrc_oas_get(m)
        mock_notification_send(m, status_code=403)
        gebruiksrechten = GebruiksrechtenFactory.create()

        url = reverse(gebruiksrechten)

        with self.assertRaises(NotificationException):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(StatusLog.objects.count(), 1)

        logged_warning = StatusLog.objects.get()
        failed = FailedNotification.objects.get()
        eio = EnkelvoudigInformatieObject.objects.get()
        message = {
            "aanmaakdatum": "2019-01-01T12:00:00Z",
            "actie": "destroy",
            "hoofdObject": f"http://testserver{reverse(eio)}",
            "kanaal": "documenten",
            "kenmerken": {
                "bronorganisatie": eio.bronorganisatie,
                "informatieobjecttype": f"http://testserver{reverse(eio.informatieobjecttype)}",
                "vertrouwelijkheidaanduiding": eio.vertrouwelijkheidaanduiding,
            },
            "resource": "gebruiksrechten",
            "resourceUrl": f"http://testserver{url}",
        }

        self.assertEqual(failed.statuslog_ptr, logged_warning)
        self.assertEqual(failed.message, message)
