"""Test d'intégration de bout en bout (SCRUM-63) : parcours complet de démonstration dans un vrai navigateur.

Prérequis : serveur lancé (python manage.py runserver) sur une base chargée avec `charger_demo --reset`.
Usage : python scripts/parcours_e2e.py [URL] [DOSSIER_CAPTURES]
Chaque étape est vérifiée ; le script s'arrête à la première anomalie.
"""
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
SORTIE = Path(sys.argv[2] if len(sys.argv) > 2 else "captures")
SORTIE.mkdir(parents=True, exist_ok=True)
MDP = "MotDePasse!2026"
SUFFIXE = datetime.now().strftime("%H%M%S")
resultats = []


def etape(nom):
    def deco(f):
        def g(*a, **k):
            debut = time.time()
            f(*a, **k)
            resultats.append((nom, round(time.time() - debut, 2)))
            print(f"OK  {nom}")
        return g
    return deco


def capture(page, nom):
    page.screenshot(path=str(SORTIE / f"{nom}.png"), full_page=True)


def connexion(page, username, mdp="footbook2026"):
    page.goto(f"{BASE}/comptes/connexion/")
    page.fill("#id_username", username)
    page.fill("#id_password", mdp)
    page.click("button[type=submit]")
    expect(page.locator("h1")).to_have_text("Tableau de bord")


def deconnexion(page):
    page.click("text=Déconnexion")
    expect(page).to_have_url(f"{BASE}/")


def inscrire(page, username, prenom, role):
    page.goto(f"{BASE}/comptes/inscription/")
    page.check(f"input[name=role][value={role}]")
    page.fill("#id_first_name", prenom)
    page.fill("#id_last_name", "Démo")
    page.fill("#id_username", username)
    page.fill("#id_email", f"{username}@footbook.test")
    page.fill("#id_password1", MDP)
    page.fill("#id_password2", MDP)
    page.click("button[type=submit]")
    expect(page.locator(".alert")).to_contain_text("votre compte est créé")


def main():
    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page(viewport={"width": 1440, "height": 900}, locale="fr-FR")
        erreurs = []
        page.on("console", lambda m: erreurs.append(m.text) if m.type == "error" else None)

        proprio, joueur = f"proprio_{SUFFIXE}", f"joueur_{SUFFIXE}"
        nom_terrain = f"Terrain Démo {SUFFIXE}"

        @etape("E1 Accueil visiteur")
        def accueil():
            page.goto(BASE)
            expect(page.locator("h1")).to_contain_text("Réservez un terrain")
            capture(page, "01_accueil")

        @etape("E2 Accès protégé : visiteur renvoyé vers la connexion (TV-05)")
        def protege():
            page.goto(f"{BASE}/terrains/")
            expect(page).to_have_url(f"{BASE}/comptes/connexion/?next=/terrains/")
            capture(page, "02_connexion")

        @etape("E3 Inscription d'un propriétaire (TV-01)")
        def insc_proprio():
            page.goto(f"{BASE}/comptes/inscription/")
            capture(page, "03_inscription")
            inscrire(page, proprio, "Nadia", "PROPRIETAIRE")
            capture(page, "04_tableau_de_bord_proprietaire")

        @etape("E4 Ajout d'un terrain, refus du prix nul (TV-07, TV-08)")
        def ajout_terrain():
            page.goto(f"{BASE}/terrains/ajouter/")
            page.fill("#id_nom", nom_terrain)
            page.select_option("#id_categorie", "5V5")
            page.select_option("#id_zone", "MAARIF")
            page.fill("#id_prix", "0")
            page.fill("#id_adresse", "1 rue de la démo")
            page.click(".contenu button[type=submit]")
            expect(page.locator(".erreur").first).to_be_visible()
            capture(page, "05_ajout_terrain_erreur")
            page.fill("#id_prix", "180")
            page.click(".contenu button[type=submit]")
            expect(page.locator("table")).to_contain_text(nom_terrain)
            capture(page, "06_mes_terrains")

        @etape("E5 Joueur : 403 sur les pages propriétaire (TV-06)")
        def refus():
            deconnexion(page)
            inscrire(page, joueur, "Omar", "JOUEUR")
            r = page.goto(f"{BASE}/terrains/mes-terrains/")
            assert r.status == 403, r.status
            capture(page, "07_403")

        @etape("E6 Recherche filtrée (TV-11)")
        def recherche():
            page.goto(f"{BASE}/terrains/?categorie=5V5&zone=MAARIF&prix_max=200")
            expect(page.locator("body")).to_contain_text(nom_terrain)
            capture(page, "08_recherche")

        code = {}

        @etape("E7 Réservation d'un créneau et QR code (TV-13, TV-16)")
        def reserver():
            page.click(f".carte:has-text('{nom_terrain}') >> text=Réserver")
            expect(page.locator("h1")).to_contain_text("Réserver")
            creneaux = page.locator(".creneaux label")
            if creneaux.count() == 0:  # plus de créneau aujourd'hui : le lendemain (la validation sera alors refusée, cas V4)
                page.locator(".jours a").nth(1).click()
            capture(page, "09_reserver")
            page.locator(".creneaux label").last.click()
            page.click("text=Confirmer la réservation")
            expect(page.locator("h1")).to_have_text("QR code de la réservation")
            expect(page.locator(".qr svg")).to_be_visible()
            code["valeur"] = page.locator(".code-texte").inner_text().strip()
            code["aujourdhui"] = datetime.now().strftime("%-d") in page.locator("table").inner_text()
            capture(page, "10_qr_code")

        @etape("E8 Publication d'une annonce (TV-23)")
        def annonce():
            page.click("text=Publier une annonce pour ce match")
            page.fill("#id_joueurs_manquants", "1")
            page.fill("#id_description", "Il nous manque un gardien.")
            capture(page, "11_publier_annonce")
            page.click("text=Publier l'annonce")
            expect(page.locator("body")).to_contain_text("Il nous manque un gardien.")
            page.goto(f"{BASE}/reservations/")
            capture(page, "12_mes_reservations")

        @etape("E9 Un autre joueur rejoint, l'annonce se ferme (TV-25)")
        def rejoindre():
            deconnexion(page)
            connexion(page, "joueur2")
            page.goto(f"{BASE}/annonces/")
            capture(page, "13_annonces")
            page.click(f".carte:has-text('Il nous manque un gardien.') >> button:has-text('Rejoindre')")
            expect(page.locator(".alert")).to_contain_text("Vous avez rejoint")
            expect(page.locator("body")).not_to_contain_text("Il nous manque un gardien.")

        @etape("E10 Réservations reçues du propriétaire (TV-21)")
        def recues():
            deconnexion(page)
            connexion(page, proprio, MDP)
            page.goto(f"{BASE}/reservations/recues/")
            expect(page.locator("table")).to_contain_text("Omar Démo")
            capture(page, "14_reservations_recues")

        @etape("E11 Code invalide, validation, second scan refusé (TV-18, TV-19, TV-20)")
        def valider():
            page.goto(f"{BASE}/reservations/valider/")
            page.fill("#id_code", "mauvais")
            page.click("#form-validation button")
            expect(page.locator(".ko-boite")).to_contain_text("Code invalide")
            page.fill("#id_code", code["valeur"])
            page.click("#form-validation button")
            if code["aujourdhui"]:
                expect(page.locator(".ok-boite")).to_contain_text("Réservation validée")
                capture(page, "15_validation_ok")
                page.fill("#id_code", code["valeur"])
                page.click("#form-validation button")
                expect(page.locator(".ko-boite")).to_contain_text("déjà validée")
                capture(page, "16_validation_deja_validee")
            else:
                expect(page.locator(".ko-boite")).to_contain_text("prévue le")
                capture(page, "15_validation_autre_jour")

        @etape("E12 Matchs joués à 1 et profil sans email (TV-27, TV-28)")
        def profil():
            deconnexion(page)
            connexion(page, joueur, MDP)
            attendu = "1" if code["aujourdhui"] else "0"
            expect(page.locator(".stat .valeur").first).to_have_text(attendu)
            capture(page, "17_tableau_de_bord_joueur")
            page.click(".sidebar >> text=Mon profil")
            expect(page.locator("body")).not_to_contain_text(f"{joueur}@footbook.test")
            capture(page, "18_profil")

        for f in (accueil, protege, insc_proprio, ajout_terrain, refus, recherche, reserver, annonce,
                  rejoindre, recues, valider, profil):
            f()
        nav.close()

    print(f"\n{len(resultats)} étapes réussies.")
    bloquantes = [e for e in erreurs if "camera" not in e.lower() and "NotAllowed" not in e and "NotFound" not in e]
    print("Erreurs console :", bloquantes or "aucune")


if __name__ == "__main__":
    main()
