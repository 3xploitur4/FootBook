"""TS1 (SCRUM-52) : gestion des terrains (US-02) et recherche (US-03)."""
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comptes.models import Role
from comptes.tests import creer
from reservations.models import Reservation

from .models import Categorie, Terrain, Zone


def terrain(proprio, nom="Terrain 1", categorie=Categorie.FOOT_5, zone=Zone.MAARIF, prix="200"):
    return Terrain.objects.create(proprietaire=proprio, nom=nom, categorie=categorie, zone=zone,
                                  prix=Decimal(prix), adresse="12 rue exemple")


class GestionTerrainsTests(TestCase):
    def setUp(self):
        self.proprio = creer("proprio", Role.PROPRIETAIRE)
        self.autre = creer("autre", Role.PROPRIETAIRE)
        self.client.force_login(self.proprio)

    def donnees(self, **kw):
        d = {"nom": "Terrain Neuf", "categorie": "5V5", "zone": "ANFA", "prix": "250", "adresse": "1 rue"}
        d.update(kw)
        return d

    def test_ajout_valide_impose_le_proprietaire(self):  # R6
        r = self.client.post(reverse("ajouter_terrain"), self.donnees(proprietaire=self.autre.pk))
        self.assertRedirects(r, reverse("mes_terrains"))
        self.assertEqual(Terrain.objects.get(nom="Terrain Neuf").proprietaire, self.proprio)

    def test_prix_nul_ou_negatif_refuse(self):  # R4
        for prix in ("0", "-10"):
            r = self.client.post(reverse("ajouter_terrain"), self.donnees(prix=prix))
            self.assertEqual(r.status_code, 200)
        self.assertFalse(Terrain.objects.exists())

    def test_nom_en_double_refuse_pour_le_meme_proprietaire(self):  # R5
        terrain(self.proprio, nom="Terrain Neuf")
        r = self.client.post(reverse("ajouter_terrain"), self.donnees(nom="terrain neuf"))
        self.assertContains(r, "Vous avez déjà un terrain portant ce nom.")

    def test_meme_nom_accepte_pour_un_autre_proprietaire(self):
        terrain(self.autre, nom="Terrain Neuf")
        self.client.post(reverse("ajouter_terrain"), self.donnees())
        self.assertEqual(Terrain.objects.filter(nom="Terrain Neuf").count(), 2)

    def test_mes_terrains_ne_montre_que_les_siens(self):
        terrain(self.proprio, nom="A moi")
        terrain(self.autre, nom="Pas a moi")
        r = self.client.get(reverse("mes_terrains"))
        self.assertContains(r, "A moi")
        self.assertNotContains(r, "Pas a moi")

    def test_modifier_ou_supprimer_le_terrain_d_un_autre_404(self):  # A4
        t = terrain(self.autre)
        self.assertEqual(self.client.get(reverse("modifier_terrain", args=[t.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("supprimer_terrain", args=[t.pk])).status_code, 404)

    def test_modifier_son_terrain(self):
        t = terrain(self.proprio)
        self.client.post(reverse("modifier_terrain", args=[t.pk]), self.donnees(nom="Renomme", prix="300"))
        t.refresh_from_db()
        self.assertEqual((t.nom, t.prix), ("Renomme", Decimal("300")))

    def test_supprimer_son_terrain(self):
        t = terrain(self.proprio)
        self.client.post(reverse("supprimer_terrain", args=[t.pk]))
        self.assertFalse(Terrain.objects.filter(pk=t.pk).exists())

    def test_terrain_reserve_non_supprimable(self):
        t = terrain(self.proprio)
        Reservation.objects.create(terrain=t, joueur=creer("joueur"),
                                   date=timezone.localdate() + timedelta(days=1), heure="18:00")
        r = self.client.post(reverse("supprimer_terrain", args=[t.pk]), follow=True)
        self.assertContains(r, "ne peut pas être supprimé")
        self.assertTrue(Terrain.objects.filter(pk=t.pk).exists())

    def test_contraintes_en_base(self):
        with self.assertRaises(IntegrityError):
            terrain(self.proprio, nom="Gratuit", prix="0")

    def test_suppression_du_proprietaire_supprime_ses_terrains(self):  # R7
        terrain(self.autre)
        self.autre.delete()
        self.assertFalse(Terrain.objects.exists())


class RechercheTests(TestCase):
    def setUp(self):
        p = creer("proprio", Role.PROPRIETAIRE)
        terrain(p, "A", Categorie.FOOT_5, Zone.MAARIF, "150")
        terrain(p, "B", Categorie.FOOT_5, Zone.ANFA, "300")
        terrain(p, "C", Categorie.FOOT_7, Zone.MAARIF, "400")
        terrain(p, "D", Categorie.FOOT_11, Zone.ANFA, "800")
        self.client.force_login(creer("joueur"))

    def noms(self, **params):
        r = self.client.get(reverse("terrains"), params)
        return [t.nom for t in r.context["terrains"]], r

    def test_sans_filtre_tous_tries_par_prix(self):
        noms, r = self.noms()
        self.assertEqual(noms, ["A", "B", "C", "D"])
        self.assertContains(r, "4 terrains")

    def test_chaque_filtre_seul(self):
        self.assertEqual(self.noms(categorie="5V5")[0], ["A", "B"])
        self.assertEqual(self.noms(zone="MAARIF")[0], ["A", "C"])
        self.assertEqual(self.noms(prix_min="300")[0], ["B", "C", "D"])
        self.assertEqual(self.noms(prix_max="300")[0], ["A", "B"])

    def test_filtres_combines(self):
        self.assertEqual(self.noms(categorie="5V5", zone="ANFA", prix_max="500")[0], ["B"])

    def test_aucun_resultat(self):
        noms, r = self.noms(categorie="11V11", zone="MAARIF")
        self.assertEqual(noms, [])
        self.assertContains(r, "Aucun terrain trouvé")

    def test_prix_min_superieur_au_max(self):
        noms, r = self.noms(prix_min="500", prix_max="100")
        self.assertEqual(len(noms), 4)
        self.assertContains(r, "Le prix minimum dépasse le prix maximum.")

    def test_valeur_hors_liste(self):
        noms, r = self.noms(zone="XYZ")
        self.assertEqual(len(noms), 4)
        self.assertTrue(r.context["form"].errors)

    def test_une_seule_requete_pour_la_liste(self):
        with self.assertNumQueries(3):  # session + utilisateur + terrains
            self.client.get(reverse("terrains"), {"categorie": "5V5", "zone": "ANFA"})
