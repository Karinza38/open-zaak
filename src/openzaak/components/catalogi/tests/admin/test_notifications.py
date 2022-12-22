# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2019 - 2020 Dimpact
from unittest.mock import patch

from django.test import override_settings, tag
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from notifications_api_common.tests.utils import mock_notify

from openzaak.accounts.tests.factories import SuperUserFactory
from openzaak.notifications.tests.mixins import NotificationsConfigMixin
from openzaak.selectielijst.models import ReferentieLijstConfig
from openzaak.selectielijst.tests import (
    mock_resource_get,
    mock_resource_list,
    mock_selectielijst_oas_get,
)
from openzaak.selectielijst.tests.mixins import ReferentieLijstServiceMixin
from openzaak.tests.utils import ClearCachesMixin, mock_nrc_oas_get

from ...models import ZaakType
from ..factories import (
    BesluitTypeFactory,
    CatalogusFactory,
    InformatieObjectTypeFactory,
    ZaakTypeFactory,
)


@tag("notifications")
@override_settings(NOTIFICATIONS_DISABLED=False)
@requests_mock.Mocker()
@patch(
    "notifications_api_common.viewsets.NotificationViewSetMixin.send_notification.delay",
    side_effect=mock_notify,
)
class NotificationAdminTests(
    NotificationsConfigMixin, ReferentieLijstServiceMixin, ClearCachesMixin, WebTest
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # there are TransactionTestCases that truncate the DB, so we need to ensure
        # there are available years
        config = ReferentieLijstConfig.get_solo()
        config.allowed_years = [2017, 2020]
        config.save()

        cls.user = SuperUserFactory.create()

    def setUp(self):
        super().setUp()
        self.catalogus = CatalogusFactory.create()

        self.app.set_user(self.user)

    def test_informatieobjecttype_notify_on_create(self, m, mock_notif):
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        url = reverse("admin:catalogi_informatieobjecttype_add")

        response = self.app.get(url)

        form = response.forms["informatieobjecttype_form"]
        form["omschrijving"] = "different-test"
        form["datum_begin_geldigheid"] = "2019-01-01"
        form["catalogus"] = self.catalogus.pk
        form["vertrouwelijkheidaanduiding"].select("openbaar")

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        called_urls = [item.url for item in m.request_history]
        self.assertIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

    def test_informatieobjecttype_notify_on_change(self, m, mock_notif):
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        informatieobjecttype = InformatieObjectTypeFactory.create(
            concept=True, omschrijving="test", vertrouwelijkheidaanduiding="openbaar"
        )
        url = reverse(
            "admin:catalogi_informatieobjecttype_change",
            args=(informatieobjecttype.pk,),
        )

        response = self.app.get(url)
        form = response.forms["informatieobjecttype_form"]
        form["omschrijving"] = "different-test"

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        called_urls = [item.url for item in m.request_history]
        self.assertIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

    def test_no_informatieobjecttype_notify_on_no_change(self, m, mock_notif):
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        informatieobjecttype = InformatieObjectTypeFactory.create(
            concept=True, omschrijving="test", vertrouwelijkheidaanduiding="openbaar"
        )
        url = reverse(
            "admin:catalogi_informatieobjecttype_change",
            args=(informatieobjecttype.pk,),
        )

        response = self.app.get(url)
        form = response.forms["informatieobjecttype_form"]

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        self.assertFalse(m.called)

    def test_besluittype_notify_on_create(self, m, mock_notif):
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_selectielijst_oas_get(m)
        mock_resource_list(m, "procestypen")
        mock_resource_get(m, "procestypen", procestype_url)
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        url = reverse("admin:catalogi_besluittype_add")

        response = self.app.get(url)

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
        )

        form = response.forms["besluittype_form"]
        form["datum_begin_geldigheid"] = "2019-01-01"
        form["zaaktypen"] = zaaktype.id
        form["catalogus"] = self.catalogus.pk

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        called_urls = [item.url for item in m.request_history]
        self.assertIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

    def test_besluit_notify_on_change(self, m, mock_notif):
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        besluit = BesluitTypeFactory.create(concept=True, omschrijving="test")
        url = reverse("admin:catalogi_besluittype_change", args=(besluit.pk,))

        response = self.app.get(url)
        form = response.forms["besluittype_form"]
        form["omschrijving"] = "different-test"

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        called_urls = [item.url for item in m.request_history]
        self.assertIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

    def test_besluit_no_notify_on_no_change(self, m, mock_notif):
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        besluit = BesluitTypeFactory.create(concept=True, omschrijving="test")
        url = reverse("admin:catalogi_besluittype_change", args=(besluit.pk,))

        response = self.app.get(url)
        form = response.forms["besluittype_form"]

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        self.assertFalse(m.called)

    def test_zaaktype_notify_on_create(self, m, mock_notif):
        mock_selectielijst_oas_get(m)
        mock_resource_list(m, "procestypen")
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        url = reverse("admin:catalogi_zaaktype_add")

        response = self.app.get(url)

        form = response.forms["zaaktype_form"]
        form["zaaktype_omschrijving"] = "test"
        form["doel"] = "test"
        form["aanleiding"] = "test"
        form["indicatie_intern_of_extern"].select("intern")
        form["handeling_initiator"] = "test"
        form["onderwerp"] = "test"
        form["handeling_behandelaar"] = "test"
        form["doorlooptijd_behandeling_days"] = 12
        form["opschorting_en_aanhouding_mogelijk"].select(False)
        form["verlenging_mogelijk"].select(False)
        form["vertrouwelijkheidaanduiding"].select("openbaar")
        form["producten_of_diensten"] = "https://example.com/foobarbaz"
        form["referentieproces_naam"] = "test"
        form["catalogus"] = self.catalogus.pk
        form["datum_begin_geldigheid"] = "21-11-2019"

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        called_urls = [item.url for item in m.request_history]
        self.assertIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

    def test_zaaktype_notify_on_change(self, m, mock_notif):
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_selectielijst_oas_get(m)
        mock_resource_list(m, "procestypen")
        mock_resource_get(m, "procestypen", procestype_url)
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
        )
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)
        form = response.forms["zaaktype_form"]
        form["zaaktype_omschrijving"] = "different-test"

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        called_urls = [item.url for item in m.request_history]
        self.assertIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

    def test_zaaktype_no_notify_on_no_change(self, m, mock_notif):
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_selectielijst_oas_get(m)
        mock_resource_list(m, "procestypen")
        mock_resource_get(m, "procestypen", procestype_url)
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
        )
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)
        form = response.forms["zaaktype_form"]

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_save")

        called_urls = [item.url for item in m.request_history]
        self.assertNotIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

    def test_zaaktype_notify_correct_resource_url_on_new_version(self, m, mock_notif):
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_selectielijst_oas_get(m)
        mock_resource_list(m, "procestypen")
        mock_resource_get(m, "procestypen", procestype_url)
        mock_nrc_oas_get(m)
        m.post(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", status_code=201
        )

        zaaktype_old = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
        )
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype_old.pk,))

        response = self.app.get(url)
        form = response.form
        form["datum_einde_geldigheid"] = "2021-01-01"

        with self.captureOnCommitCallbacks(execute=True):
            form.submit("_addversion")

        called_urls = [item.url for item in m.request_history]
        self.assertIn(
            "https://notificaties-api.vng.cloud/api/v1/notificaties", called_urls
        )

        zaaktype_old.refresh_from_db()

        zaaktype_new = ZaakType.objects.exclude(pk=zaaktype_old.pk).get()

        last_request = m.request_history[-1]
        last_request_data = last_request.json()
        self.assertEqual(
            f"http://testserver{zaaktype_new.get_absolute_api_url()}",
            last_request_data["resourceUrl"],
        )
