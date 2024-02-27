# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2019 - 2020 Dimpact
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import WebTest
from freezegun import freeze_time

from openzaak.accounts.tests.factories import SuperUserFactory, UserFactory
from openzaak.notifications.tests.mixins import NotificationsConfigMixin
from openzaak.selectielijst.models import ReferentieLijstConfig
from openzaak.selectielijst.tests import (
    mock_resource_get,
    mock_resource_list,
    mock_selectielijst_oas_get,
)
from openzaak.selectielijst.tests.mixins import ReferentieLijstServiceMixin
from openzaak.tests.utils import ClearCachesMixin

from ..factories import (
    BesluitTypeFactory,
    CatalogusFactory,
    InformatieObjectTypeFactory,
    ResultaatTypeFactory,
    RolTypeFactory,
    StatusTypeFactory,
    ZaakTypeFactory,
    ZaakTypeInformatieObjectTypeFactory,
)


@requests_mock.Mocker()
class ZaaktypeAdminTests(
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

        self.app.set_user(self.user)

    @tag("notifications")
    @override_settings(NOTIFICATIONS_DISABLED=False)
    @freeze_time("2022-01-01")
    @patch("notifications_api_common.viewsets.send_notification.delay")
    def test_publish_zaaktype(self, m, mock_notif):
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_selectielijst_oas_get(m)
        mock_resource_list(m, "procestypen")
        mock_resource_get(m, "procestypen", procestype_url)
        selectielijst_resultaat = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "resultaten/cc5ae4e3-a9e6-4386-bcee-46be4986a829"
        )
        mock_resource_get(m, "resultaten", url=selectielijst_resultaat)

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
            verlenging_mogelijk=False,
        )
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=1)
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=2)
        ResultaatTypeFactory.create(
            zaaktype=zaaktype, selectielijstklasse=selectielijst_resultaat
        )
        RolTypeFactory.create(zaaktype=zaaktype)
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        url = reverse("admin:catalogi_zaaktype_publish", args=(zaaktype.pk,))
        publish_page = self.app.get(url)

        with self.captureOnCommitCallbacks(execute=True):
            response = publish_page.form.submit("_publish").follow()

        zaaktype.refresh_from_db()
        self.assertFalse(zaaktype.concept)

        # Verify that the publish button is disabled
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNotNone(publish_button)

        # Verify notification is sent
        zaaktype_url = reverse(
            "zaaktype-detail", kwargs={"uuid": zaaktype.uuid, "version": 1}
        )
        catalogus_url = reverse(
            "catalogus-detail", kwargs={"uuid": zaaktype.catalogus.uuid, "version": 1},
        )
        mock_notif.assert_called_with(
            {
                "kanaal": "zaaktypen",
                "hoofdObject": f"http://testserver{zaaktype_url}",
                "resource": "zaaktype",
                "resourceUrl": f"http://testserver{zaaktype_url}",
                "actie": "update",
                "aanmaakdatum": "2022-01-01T00:00:00Z",
                "kenmerken": {"catalogus": f"http://testserver{catalogus_url}"},
            }
        )

    def test_publish_besluittype(self, m):
        besluittype = BesluitTypeFactory.create(concept=True)
        url = reverse("admin:catalogi_besluittype_change", args=(besluittype.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        form = response.forms["besluittype_form"]

        response = form.submit("_publish").follow()

        besluittype.refresh_from_db()
        self.assertFalse(besluittype.concept)

        # Verify that the publish button is disabled
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNotNone(publish_button)

    def test_publish_informatieobjecttype(self, m):
        iot = InformatieObjectTypeFactory.create(
            concept=True, vertrouwelijkheidaanduiding="openbaar"
        )
        iot.zaaktypeinformatieobjecttype_set.all().delete()
        url = reverse("admin:catalogi_informatieobjecttype_change", args=(iot.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        form = response.forms["informatieobjecttype_form"]

        response = form.submit("_publish").follow()

        iot.refresh_from_db()
        self.assertFalse(iot.concept)

        # Verify that the publish button is disabled
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNotNone(publish_button)

    def test_publish_zaaktype_related_to_concept_besluittype_fails(self, m):
        mock_selectielijst_oas_get(m)
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_resource_list(m, "procestypen")
        selectielijst_resultaat = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "resultaten/cc5ae4e3-a9e6-4386-bcee-46be4986a829"
        )
        mock_resource_get(m, "resultaten", url=selectielijst_resultaat)

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
            verlenging_mogelijk=False,
        )
        BesluitTypeFactory.create(concept=True, zaaktypen=[zaaktype])
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=1)
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=2)
        ResultaatTypeFactory.create(
            zaaktype=zaaktype, selectielijstklasse=selectielijst_resultaat
        )
        RolTypeFactory.create(zaaktype=zaaktype)
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        url = reverse("admin:catalogi_zaaktype_publish", args=(zaaktype.pk,))
        publish_page = self.app.get(url)
        response = publish_page.form.submit("_publish")
        # returns same page on fail
        self.assertEqual(response.status_code, 200)

        zaaktype.refresh_from_db()
        self.assertTrue(zaaktype.concept)

        # Check that the error is shown on the page
        error_message = response.html.find("li", {"class": "error"})
        self.assertIn(
            _("All related resources should be published"), error_message.text
        )

        # Verify that the publish button is still visible and enabled.
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

    def test_publish_zaaktype_related_to_concept_besluittype_succeeds(self, m):
        mock_selectielijst_oas_get(m)
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_resource_list(m, "procestypen")
        mock_resource_get(m, "procestypen", procestype_url)
        selectielijst_resultaat = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "resultaten/cc5ae4e3-a9e6-4386-bcee-46be4986a829"
        )
        mock_resource_get(m, "resultaten", url=selectielijst_resultaat)

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
            verlenging_mogelijk=False,
        )
        besluit_type = BesluitTypeFactory.create(concept=True, zaaktypen=[zaaktype])
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=1)
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=2)
        ResultaatTypeFactory.create(
            zaaktype=zaaktype, selectielijstklasse=selectielijst_resultaat
        )
        RolTypeFactory.create(zaaktype=zaaktype)
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        url = reverse("admin:catalogi_zaaktype_publish", args=(zaaktype.pk,))
        publish_page = self.app.get(url)
        publish_page.form["_auto-publish"] = True
        response = publish_page.form.submit().follow()
        # redirects on success
        self.assertEqual(response.status_code, 200)

        zaaktype.refresh_from_db()
        self.assertFalse(zaaktype.concept)
        besluit_type.refresh_from_db()
        self.assertFalse(besluit_type.concept)

        messages = list(response.context["messages"])
        self.assertEqual(
            str(messages[0]),
            _("Auto-published related besluittypen: {besluittypen}").format(
                besluittypen=besluit_type.omschrijving
            ),
        )

        # Verify that the publish button is disabled.
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNotNone(publish_button)

    def test_publish_zaaktype_related_to_concept_informatieobjecttype_fails(self, m):
        mock_selectielijst_oas_get(m)
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_resource_list(m, "procestypen")
        selectielijst_resultaat = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "resultaten/cc5ae4e3-a9e6-4386-bcee-46be4986a829"
        )
        mock_resource_get(m, "resultaten", url=selectielijst_resultaat)

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
            verlenging_mogelijk=False,
        )
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=1)
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=2)
        ResultaatTypeFactory.create(
            zaaktype=zaaktype, selectielijstklasse=selectielijst_resultaat
        )
        RolTypeFactory.create(zaaktype=zaaktype)
        ZaakTypeInformatieObjectTypeFactory.create(
            informatieobjecttype__concept=True, zaaktype=zaaktype
        )
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        url = reverse("admin:catalogi_zaaktype_publish", args=(zaaktype.pk,))
        publish_page = self.app.get(url)
        response = publish_page.form.submit("_publish")
        # returns same page on fail
        self.assertEqual(response.status_code, 200)

        zaaktype.refresh_from_db()
        self.assertTrue(zaaktype.concept)

        # Check that the error is shown on the page
        error_message = response.html.find("li", {"class": "error"})
        self.assertIn(
            _("All related resources should be published"), error_message.text
        )

        # Verify that the publish button is still visible and enabled.
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

    def test_publish_zaaktype_related_to_concept_informatieobjecttype_succeeds(self, m):
        mock_selectielijst_oas_get(m)
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_resource_list(m, "procestypen")
        mock_resource_get(m, "procestypen", procestype_url)
        selectielijst_resultaat = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "resultaten/cc5ae4e3-a9e6-4386-bcee-46be4986a829"
        )
        mock_resource_get(m, "resultaten", url=selectielijst_resultaat)

        zaaktype = ZaakTypeFactory.create(
            concept=True,
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
            verlenging_mogelijk=False,
        )
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=1)
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=2)
        ResultaatTypeFactory.create(
            zaaktype=zaaktype, selectielijstklasse=selectielijst_resultaat
        )
        RolTypeFactory.create(zaaktype=zaaktype)

        informatieobjecttype = InformatieObjectTypeFactory.create(
            catalogus=zaaktype.catalogus, zaaktypen__zaaktype=zaaktype, concept=True,
        )
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        url = reverse("admin:catalogi_zaaktype_publish", args=(zaaktype.pk,))
        publish_page = self.app.get(url)
        publish_page.form["_auto-publish"] = True
        response = publish_page.form.submit().follow()
        # redirects on success
        self.assertEqual(response.status_code, 200)

        zaaktype.refresh_from_db()
        self.assertFalse(zaaktype.concept)
        informatieobjecttype.refresh_from_db()
        self.assertFalse(informatieobjecttype.concept)

        messages = list(response.context["messages"])
        self.assertEqual(
            str(messages[0]),
            _("Auto-published related informatieobjecttypen: {iots}").format(
                iots=informatieobjecttype.omschrijving
            ),
        )

        # Verify that the publish button is disabled.
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNotNone(publish_button)


@requests_mock.Mocker()
class PublishWithGeldigheidTests(
    ReferentieLijstServiceMixin, ClearCachesMixin, WebTest
):
    def setUp(self):
        self.user = SuperUserFactory.create()
        self.app.set_user(self.user)

    def test_publish_zaaktype_with_existing_overlap_fails(self, m):
        mock_selectielijst_oas_get(m)
        procestype_url = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "procestypen/e1b73b12-b2f6-4c4e-8929-94f84dd2a57d"
        )
        mock_resource_list(m, "procestypen")
        selectielijst_resultaat = (
            "https://selectielijst.openzaak.nl/api/v1/"
            "resultaten/cc5ae4e3-a9e6-4386-bcee-46be4986a829"
        )
        mock_resource_get(m, "resultaten", url=selectielijst_resultaat)

        catalogus = CatalogusFactory()

        old_zaaktype = ZaakTypeFactory.create(
            catalogus=catalogus,
            concept=False,
            identificatie="Justin-Case",
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
            verlenging_mogelijk=False,
            datum_begin_geldigheid="2018-01-01",
            datum_einde_geldigheid=None,
        )

        zaaktype = ZaakTypeFactory.create(
            catalogus=catalogus,
            concept=True,
            identificatie="Justin-Case",
            zaaktype_omschrijving="test",
            vertrouwelijkheidaanduiding="openbaar",
            trefwoorden=["test"],
            verantwoordingsrelatie=["bla"],
            selectielijst_procestype=procestype_url,
            verlenging_mogelijk=False,
            datum_begin_geldigheid="2018-01-10",
            datum_einde_geldigheid=None,
        )
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=1)
        StatusTypeFactory.create(zaaktype=zaaktype, statustypevolgnummer=2)
        ResultaatTypeFactory.create(
            zaaktype=zaaktype, selectielijstklasse=selectielijst_resultaat
        )
        RolTypeFactory.create(zaaktype=zaaktype)

        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        response = self.app.get(url)

        # Verify that the publish button is visible and enabled
        publish_button = response.html.find("input", {"name": "_publish"})
        self.assertIsNotNone(publish_button)
        publish_button = response.html.find(
            "input", {"name": "_publish", "disabled": "disabled"}
        )
        self.assertIsNone(publish_button)

        form = response.forms["zaaktype_form"]

        response = form.submit("_publish")
        error_message = response.html.find(class_="errorlist")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f"{zaaktype._meta.verbose_name} versies (dezelfde omschrijving) mogen geen overlappende "
            "geldigheid hebben.",
            error_message.text,
        )
        zaaktype.refresh_from_db()
        self.assertTrue(zaaktype.concept)

        old_zaaktype.datum_einde_geldigheid = "2018-01-09"
        old_zaaktype.save()

        response = form.submit("_publish")

        self.assertEqual(response.status_code, 302)
        zaaktype.refresh_from_db()
        self.assertFalse(zaaktype.concept)


@tag("readonly-user")
class ReadOnlyUserTests(ClearCachesMixin, WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user = UserFactory.create(is_staff=True)
        view_zaaktype = Permission.objects.get(codename="view_zaaktype")
        view_informatieobjecttype = Permission.objects.get(
            codename="view_informatieobjecttype"
        )
        view_besluittype = Permission.objects.get(codename="view_besluittype")
        user.user_permissions.add(
            view_zaaktype, view_informatieobjecttype, view_besluittype
        )

        cls.user = user

    def setUp(self):
        super().setUp()
        self.app.set_user(self.user)

    def test_zaaktype_publish_not_possible(self):
        zaaktype = ZaakTypeFactory.create(concept=True)
        url = reverse("admin:catalogi_zaaktype_change", args=(zaaktype.pk,))

        detail_page = self.app.get(url)

        html = detail_page.form.html
        self.assertNotIn(_("Publiceren"), html)

        # try to submit it anyway
        detail_page.form.submit("_publish", status=403)

    def test_informatieobjecttype_publish_not_possible(self):
        informatieobjecttype = InformatieObjectTypeFactory.create(concept=True)
        url = reverse(
            "admin:catalogi_informatieobjecttype_change",
            args=(informatieobjecttype.pk,),
        )

        detail_page = self.app.get(url)

        html = detail_page.form.html
        self.assertNotIn(_("Publiceren"), html)

        # try to submit it anyway
        detail_page.form.submit("_publish", status=403)

    def test_besluittype_publish_not_possible(self):
        besluittype = BesluitTypeFactory.create(concept=True)
        url = reverse("admin:catalogi_besluittype_change", args=(besluittype.pk,))

        detail_page = self.app.get(url)

        html = detail_page.form.html
        self.assertNotIn(_("Publiceren"), html)

        # try to submit it anyway
        detail_page.form.submit("_publish", status=403)
