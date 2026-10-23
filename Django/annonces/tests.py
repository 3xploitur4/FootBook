"""TS4 (SCRUM-61) : annonces, règles B1 à B6 (SCRUM-57)."""
from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comptes.models import Role
from comptes.tests import creer
from reservations.models import Reservation, Statut
from terrains.models import Categorie
from terrains.tests import terrain

from .models import Annonce, Participation
from .views import rejoindre


def demain():
    return timezone.localdate() + timedelta(days=1)


class PublierTests(TestCase):
    def setUp(self):
        self.terrain = terrain(creer("proprio", Role.PROPRIETAIRE), categorie=Categorie.FOOT_5)
        self.auteur = creer("auteur")
        self.res = Reservation.objects.create(terrain=self.terrain, joueur=self.auteur, date=demain(), heure=time(19))
        self.client.force_login(self.auteur)
        self.url = reverse("publier_annonce", args=[self.res.pk])

    def test_publication_valide(self):
        r = self.client.post(self.url, {"joueurs_manquants": 3, "description": "Niveau moyen"})
        self.assertRedirects(r, reverse("annonces"))
        a = Annonce.objects.get()
        self.assertEqual((a.reservation, a.joueurs_manquants, a.ouverte), (self.res, 3, True))

    def test_b1_une_seule_annonce(self):
        Annonce.objects.create(reservation=self.res, joueurs_manquants=2)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_b2_reservation_d_un_autre_404(self):
        self.client.force_login(creer("autre"))
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_b2_reservation_passee_ou_validee_404(self):
        self.res.date = timezone.localdate() - timedelta(days=1)
        self.res.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.res.date, self.res.statut = demain(), Statut.VALIDEE
        self.res.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_b3_nombre_selon_categorie(self):
        for n in (0, 10):  # 5V5 -> 1 à 9
            self.assertEqual(self.client.post(self.url, {"joueurs_manquants": n}).status_code, 200)
        self.assertFalse(Annonce.objects.exists())
        self.client.post(self.url, {"joueurs_manquants": 9})
        self.assertTrue(Annonce.objects.exists())


class RejoindreTests(TestCase):
    def setUp(self):
        self.auteur = creer("auteur")
        res = Reservation.objects.create(terrain=terrain(creer("proprio", Role.PROPRIETAIRE)),
                                         joueur=self.auteur, date=demain(), heure=time(19))
        self.annonce = Annonce.objects.create(reservation=res, joueurs_manquants=2)
        self.j1, self.j2, self.j3 = creer("j1"), creer("j2"), creer("j3")
        self.url = reverse("rejoindre", args=[self.annonce.pk])

    def test_rejoindre_decremente_et_ferme_a_zero(self):
        self.assertIsNone(rejoindre(self.annonce, self.j1))
        self.assertIsNone(rejoindre(self.annonce, self.j2))
        self.annonce.refresh_from_db()
        self.assertEqual((self.annonce.joueurs_manquants, self.annonce.ouverte), (0, False))
        self.assertNotIn(self.annonce, Annonce.ouvertes())

    def test_b4_annonce_complete(self):
        rejoindre(self.annonce, self.j1)
        rejoindre(self.annonce, self.j2)
        self.assertEqual(rejoindre(self.annonce, self.j3), "Cette annonce est complète.")
        self.assertEqual(Participation.objects.count(), 2)

    def test_b5_pas_de_double_participation(self):
        rejoindre(self.annonce, self.j1)
        self.assertEqual(rejoindre(self.annonce, self.j1), "Vous participez déjà à ce match.")
        self.annonce.refresh_from_db()
        self.assertEqual(self.annonce.joueurs_manquants, 1)  # décrément annulé avec la transaction

    def test_auteur_ne_rejoint_pas_sa_propre_annonce(self):
        self.client.force_login(self.auteur)
        self.client.post(self.url)
        self.assertFalse(Participation.objects.exists())

    def test_rejoindre_en_post_uniquement(self):  # A6
        self.client.force_login(self.j1)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertRedirects(self.client.post(self.url), reverse("annonces"))
        self.assertTrue(Participation.objects.filter(joueur=self.j1).exists())

    def test_b6_match_passe_masque_et_refuse(self):
        res = self.annonce.reservation
        res.date = timezone.localdate() - timedelta(days=1)
        res.save()
        self.assertNotIn(self.annonce, Annonce.ouvertes())
        self.client.force_login(self.j1)
        self.client.post(self.url)
        self.assertFalse(Participation.objects.exists())

    def test_liste_des_annonces(self):
        self.client.force_login(self.j1)
        r = self.client.get(reverse("annonces"))
        self.assertIn(self.annonce, r.context["annonces"])
