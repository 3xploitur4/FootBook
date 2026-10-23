"""TS1 (SCRUM-52) : comptes et accès par rôle (US-01, règles R1, R2, A1, A2)."""
from django.test import TestCase
from django.urls import reverse

from .models import Role, Utilisateur


def creer(username, role=Role.JOUEUR, **kw):
    return Utilisateur.objects.create_user(username=username, email=f"{username}@test.ma", password="MotDePasse!2026",
                                           first_name=username.capitalize(), last_name="Test", role=role, **kw)


class InscriptionTests(TestCase):
    url = reverse("inscription")

    def donnees(self, **kw):
        d = {"username": "ali_foot", "first_name": "Ali", "last_name": "Test", "email": "ali@test.ma",
             "password1": "MotDePasse!2026", "password2": "MotDePasse!2026", "role": Role.JOUEUR}
        d.update(kw)
        return d

    def test_inscription_valide_connecte_et_redirige_vers_espace(self):
        r = self.client.post(self.url, self.donnees())
        self.assertRedirects(r, reverse("espace"))
        u = Utilisateur.objects.get(username="ali_foot")
        self.assertEqual(u.matchs_joues, 0)
        self.assertEqual(u.role, Role.JOUEUR)
        self.assertTrue(u.password.startswith("pbkdf2_sha256$"))  # ENF-03 : mot de passe haché
        self.assertEqual(int(self.client.session["_auth_user_id"]), u.pk)

    def test_email_deja_utilise_refuse(self):  # R1
        creer("existant")
        r = self.client.post(self.url, self.donnees(email="EXISTANT@test.ma"))
        self.assertContains(r, "Un compte utilise déjà cette adresse email.")
        self.assertFalse(Utilisateur.objects.filter(username="ali_foot").exists())

    def test_mots_de_passe_differents_refuses(self):
        r = self.client.post(self.url, self.donnees(password2="Autre!2026xx"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Utilisateur.objects.filter(username="ali_foot").exists())

    def test_role_hors_liste_refuse(self):  # R2
        r = self.client.post(self.url, self.donnees(role="ADMIN"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Utilisateur.objects.exists())

    def test_prenom_et_nom_obligatoires(self):
        self.client.post(self.url, self.donnees(first_name="", last_name=""))
        self.assertFalse(Utilisateur.objects.exists())

    def test_utilisateur_connecte_renvoye_vers_espace(self):
        self.client.force_login(creer("joueur"))
        self.assertRedirects(self.client.get(self.url), reverse("espace"))


class ConnexionTests(TestCase):
    def setUp(self):
        self.u = creer("joueur")

    def test_connexion_reussie(self):
        r = self.client.post(reverse("connexion"), {"username": "joueur", "password": "MotDePasse!2026"})
        self.assertRedirects(r, reverse("espace"))

    def test_connexion_echouee_message(self):
        r = self.client.post(reverse("connexion"), {"username": "joueur", "password": "faux"})
        self.assertContains(r, "Nom d&#x27;utilisateur ou mot de passe incorrect.")

    def test_retour_a_la_page_demandee(self):
        r = self.client.post(reverse("connexion") + "?next=/terrains/",
                             {"username": "joueur", "password": "MotDePasse!2026", "next": "/terrains/"})
        self.assertRedirects(r, "/terrains/")

    def test_deconnexion_en_post(self):
        self.client.force_login(self.u)
        self.assertRedirects(self.client.post(reverse("deconnexion")), reverse("accueil"))
        self.assertNotIn("_auth_user_id", self.client.session)


class AccesParRoleTests(TestCase):
    """Trois tests par page : visiteur -> connexion, mauvais rôle -> 403, bon rôle -> 200 (SCRUM-50)."""

    pages_joueur = ["terrains", "mes_reservations", "annonces"]
    pages_proprietaire = ["mes_terrains", "ajouter_terrain", "reservations_recues", "valider_qr"]

    def setUp(self):
        self.joueur = creer("joueur")
        self.proprio = creer("proprio", Role.PROPRIETAIRE)

    def verifier(self, nom, bon, mauvais):
        url = reverse(nom)
        self.assertRedirects(self.client.get(url), f"{reverse('connexion')}?next={url}")
        self.client.force_login(mauvais)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(bon)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.logout()

    def test_pages_joueur(self):
        for nom in self.pages_joueur:
            with self.subTest(page=nom):
                self.verifier(nom, self.joueur, self.proprio)

    def test_pages_proprietaire(self):
        for nom in self.pages_proprietaire:
            with self.subTest(page=nom):
                self.verifier(nom, self.proprio, self.joueur)

    def test_mon_espace_pour_les_deux_roles(self):
        url = reverse("espace")
        self.assertEqual(self.client.get(url).status_code, 302)
        for u in (self.joueur, self.proprio):
            self.client.force_login(u)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_menu_selon_le_role(self):
        self.client.force_login(self.proprio)
        r = self.client.get(reverse("espace"))
        self.assertContains(r, "Mes terrains")
        self.assertNotContains(r, "Mes réservations")


class ProfilJoueurTests(TestCase):
    """TS4 (SCRUM-61) : profil (US-12, SCRUM-59)."""

    def setUp(self):
        self.joueur = creer("joueur", matchs_joues=3)
        self.autre = creer("autre")
        self.proprio = creer("proprio", Role.PROPRIETAIRE)

    def test_profil_affiche_nom_et_matchs_sans_email(self):
        self.client.force_login(self.autre)
        r = self.client.get(reverse("profil_joueur", args=[self.joueur.pk]))
        self.assertContains(r, "Joueur Test")
        self.assertContains(r, "matchs joués")
        self.assertContains(r, ">3<")
        self.assertNotContains(r, self.joueur.email)

    def test_profil_d_un_proprietaire_ou_inconnu_404(self):
        self.client.force_login(self.autre)
        self.assertEqual(self.client.get(reverse("profil_joueur", args=[self.proprio.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("profil_joueur", args=[999])).status_code, 404)

    def test_acces_reserve_aux_joueurs(self):
        url = reverse("profil_joueur", args=[self.joueur.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.proprio)
        self.assertEqual(self.client.get(url).status_code, 403)
