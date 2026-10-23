"""TS2 (SCRUM-56) et TS3 (SCRUM-58) : réservation, QR code, validation, historiques."""
from datetime import time, timedelta
from unittest import mock

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from annonces.models import Annonce, Participation
from comptes.models import Role
from comptes.tests import creer
from terrains.tests import terrain

from .creneaux import creneaux_libres, generer_code
from .models import Reservation, Statut


def demain():
    return timezone.localdate() + timedelta(days=1)


class ReservationTests(TestCase):
    def setUp(self):
        self.proprio = creer("proprio", Role.PROPRIETAIRE)
        self.terrain = terrain(self.proprio)
        self.joueur = creer("joueur")
        self.autre = creer("autre")
        self.client.force_login(self.joueur)
        self.url = reverse("reserver", args=[self.terrain.pk])

    def test_page_reserver_affiche_les_creneaux(self):
        r = self.client.get(self.url, {"date": demain().isoformat()})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["creneaux"]), 14)  # 9:00 à 22:00

    def test_reservation_valide_redirige_vers_qr(self):
        r = self.client.post(self.url, {"date": demain().isoformat(), "heure": "18:00"})
        res = Reservation.objects.get()
        self.assertRedirects(r, reverse("qr_code", args=[res.pk]))
        self.assertEqual((res.joueur, res.statut, res.heure), (self.joueur, Statut.CONFIRMEE, time(18)))
        self.assertEqual(len(res.code), 22)

    def test_creneau_deja_pris_refuse(self):  # EF-03
        Reservation.objects.create(terrain=self.terrain, joueur=self.autre, date=demain(), heure=time(18))
        r = self.client.post(self.url, {"date": demain().isoformat(), "heure": "18:00"})
        self.assertContains(r, "plus disponible")
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertNotIn(time(18), creneaux_libres(self.terrain, demain()))

    def test_double_reservation_simultanee(self):
        """Les deux joueurs passent la vérification ; la contrainte d'unicité refuse le second."""
        Reservation.objects.create(terrain=self.terrain, joueur=self.autre, date=demain(), heure=time(18))
        with mock.patch("reservations.forms.creneaux_libres", return_value=[time(18)]):
            r = self.client.post(self.url, {"date": demain().isoformat(), "heure": "18:00"})
        self.assertContains(r, "vient d&#x27;être réservé")
        self.assertEqual(Reservation.objects.count(), 1)

    def test_contrainte_unicite_en_base(self):
        Reservation.objects.create(terrain=self.terrain, joueur=self.joueur, date=demain(), heure=time(10))
        with self.assertRaises(IntegrityError):
            Reservation.objects.create(terrain=self.terrain, joueur=self.autre, date=demain(), heure=time(10))

    def test_date_et_heure_hors_plage_refusees(self):
        for donnees in ({"date": (timezone.localdate() + timedelta(days=15)).isoformat(), "heure": "18:00"},
                        {"date": (timezone.localdate() - timedelta(days=1)).isoformat(), "heure": "18:00"},
                        {"date": demain().isoformat(), "heure": "23:00"},
                        {"date": demain().isoformat(), "heure": "18:30"}):
            with self.subTest(**donnees):
                self.assertEqual(self.client.post(self.url, donnees).status_code, 200)
        self.assertFalse(Reservation.objects.exists())

    def test_le_joueur_est_impose(self):
        self.client.post(self.url, {"date": demain().isoformat(), "heure": "18:00", "joueur": self.autre.pk})
        self.assertEqual(Reservation.objects.get().joueur, self.joueur)

    def test_terrain_inconnu_404(self):
        self.assertEqual(self.client.get(reverse("reserver", args=[999])).status_code, 404)

    def test_proprietaire_ne_reserve_pas(self):
        self.client.force_login(self.proprio)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_creneaux_passes_du_jour_absents(self):  # TV-15
        maintenant = timezone.localtime().replace(hour=14, minute=30)
        with mock.patch("reservations.creneaux.timezone.localtime", return_value=maintenant):
            libres = creneaux_libres(self.terrain, maintenant.date())
        self.assertEqual(libres[0], time(15))
        self.assertNotIn(time(14), libres)

    def test_codes_uniques_et_imprevisibles(self):
        codes = {generer_code() for _ in range(500)}
        self.assertEqual(len(codes), 500)


class QRCodeTests(TestCase):
    def setUp(self):
        self.joueur = creer("joueur")
        self.res = Reservation.objects.create(terrain=terrain(creer("proprio", Role.PROPRIETAIRE)),
                                              joueur=self.joueur, date=demain(), heure=time(18))

    def test_qr_visible_par_son_joueur(self):
        self.client.force_login(self.joueur)
        r = self.client.get(reverse("qr_code", args=[self.res.pk]))
        self.assertContains(r, "<svg")
        self.assertContains(r, self.res.code)

    def test_qr_d_un_autre_joueur_404(self):  # A3
        self.client.force_login(creer("autre"))
        self.assertEqual(self.client.get(reverse("qr_code", args=[self.res.pk])).status_code, 404)


class ValidationTests(TestCase):
    """Cas V1 à V4 de SCRUM-55 et incrément de matchs_joues (SCRUM-40)."""

    def setUp(self):
        self.proprio = creer("proprio", Role.PROPRIETAIRE)
        self.terrain = terrain(self.proprio)
        self.joueur = creer("joueur")
        self.res = Reservation.objects.create(terrain=self.terrain, joueur=self.joueur,
                                              date=timezone.localdate(), heure=time(20))
        self.client.force_login(self.proprio)
        self.url = reverse("valider_qr")

    def valider(self, code):
        return self.client.post(self.url, {"code": code})

    def test_validation_reussie(self):
        r = self.valider(self.res.code)
        self.assertTrue(r.context["succes"])
        self.res.refresh_from_db()
        self.joueur.refresh_from_db()
        self.assertEqual(self.res.statut, Statut.VALIDEE)
        self.assertIsNotNone(self.res.valide_le)
        self.assertEqual(self.joueur.matchs_joues, 1)

    def test_v1_format_invalide(self):
        for code in ("", "trop-court", "x" * 23, "caractères interdits!!"):
            with self.subTest(code=code):
                self.assertEqual(self.valider(code).context["erreur"], "Code invalide.")

    def test_v2_code_inconnu(self):
        self.assertIn("Aucune réservation", self.valider("A" * 22).context["erreur"])

    def test_v2_terrain_d_un_autre_proprietaire_meme_message(self):
        self.client.force_login(creer("autre_proprio", Role.PROPRIETAIRE))
        self.assertIn("Aucune réservation", self.valider(self.res.code).context["erreur"])
        self.res.refresh_from_db()
        self.assertEqual(self.res.statut, Statut.CONFIRMEE)

    def test_v3_deja_validee(self):
        self.valider(self.res.code)
        r = self.valider(self.res.code)
        self.assertIn("déjà validée", r.context["erreur"])
        self.joueur.refresh_from_db()
        self.assertEqual(self.joueur.matchs_joues, 1)  # pas de double comptage

    def test_v4_autre_jour(self):
        self.res.date = demain()
        self.res.save()
        self.assertIn("prévue le", self.valider(self.res.code).context["erreur"])

    def test_scan_simultane_un_seul_compte(self):
        """La réservation passe en VALIDEE entre la lecture et la mise à jour : le second scan est refusé."""
        Reservation.objects.filter(pk=self.res.pk).update(statut=Statut.VALIDEE)
        with mock.patch("reservations.views.Reservation.objects.select_related") as sr:
            self.res.statut = Statut.CONFIRMEE
            sr.return_value.filter.return_value.first.return_value = self.res
            r = self.valider(self.res.code)
        self.assertEqual(r.context["erreur"], "Réservation déjà validée.")
        self.joueur.refresh_from_db()
        self.assertEqual(self.joueur.matchs_joues, 0)

    def test_participants_comptes(self):  # B7
        annonce = Annonce.objects.create(reservation=self.res, joueurs_manquants=1)
        p1, p2 = creer("p1"), creer("p2")
        Participation.objects.create(annonce=annonce, joueur=p1)
        Participation.objects.create(annonce=annonce, joueur=p2)
        self.valider(self.res.code)
        for u in (self.joueur, p1, p2):
            u.refresh_from_db()
            self.assertEqual(u.matchs_joues, 1)


class HistoriquesTests(TestCase):
    def setUp(self):
        self.proprio = creer("proprio", Role.PROPRIETAIRE)
        self.t1 = terrain(self.proprio, "Mon terrain")
        self.t2 = terrain(creer("autre_proprio", Role.PROPRIETAIRE), "Terrain etranger")
        self.joueur = creer("joueur")
        hier = timezone.localdate() - timedelta(days=1)
        self.a_venir = Reservation.objects.create(terrain=self.t1, joueur=self.joueur, date=demain(), heure=time(18))
        self.passee = Reservation.objects.create(terrain=self.t1, joueur=self.joueur, date=hier, heure=time(18))
        self.etrangere = Reservation.objects.create(terrain=self.t2, joueur=creer("autre"), date=demain(), heure=time(18))

    def test_mes_reservations_separe_a_venir_et_passees(self):  # US-08
        self.client.force_login(self.joueur)
        r = self.client.get(reverse("mes_reservations"))
        self.assertEqual(r.context["a_venir"], [self.a_venir])
        self.assertEqual(r.context["passees"], [self.passee])

    def test_reservations_recues_limitees_a_ses_terrains(self):  # US-07, A4
        self.client.force_login(self.proprio)
        r = self.client.get(reverse("reservations_recues"))
        tout = r.context["a_venir"] + r.context["passees"]
        self.assertIn(self.a_venir, tout)
        self.assertNotIn(self.etrangere, tout)
