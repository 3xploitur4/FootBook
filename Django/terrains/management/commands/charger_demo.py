"""Jeu de données de démonstration (SCRUM-29, T02.3 ; minimums de SCRUM-51).

python manage.py charger_demo           # crée les données si elles n'existent pas
python manage.py charger_demo --reset   # supprime puis recrée les comptes de démonstration
"""
from datetime import time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from annonces.models import Annonce, Participation
from comptes.models import Role, Utilisateur
from reservations.models import Reservation, Statut
from terrains.models import Categorie, Terrain, Zone

MOT_DE_PASSE = "footbook2026"

COMPTES = [
    ("proprio1", "Karim", "Exemple", Role.PROPRIETAIRE),
    ("proprio2", "Salma", "Exemple", Role.PROPRIETAIRE),
    ("joueur1", "Ali", "Exemple", Role.JOUEUR),
    ("joueur2", "Youssef", "Exemple", Role.JOUEUR),
    ("joueur3", "Imane", "Exemple", Role.JOUEUR),
]

# 12 terrains : 4 par catégorie, chacune des 12 zones une fois ; prix fictifs (SCRUM-51).
TERRAINS = [
    ("proprio1", "Terrain Maârif 5", Categorie.FOOT_5, Zone.MAARIF, "150", "12 rue exemple"),
    ("proprio1", "Terrain Anfa 5", Categorie.FOOT_5, Zone.ANFA, "200", "34 avenue exemple"),
    ("proprio2", "Terrain Aïn Diab 5", Categorie.FOOT_5, Zone.AIN_DIAB, "250", "5 corniche exemple"),
    ("proprio2", "Terrain Californie 5", Categorie.FOOT_5, Zone.CALIFORNIE, "300", "8 rue exemple"),
    ("proprio1", "Terrain Bourgogne 7", Categorie.FOOT_7, Zone.BOURGOGNE, "250", "21 rue exemple"),
    ("proprio1", "Terrain Aïn Sebaâ 7", Categorie.FOOT_7, Zone.AIN_SEBAA, "300", "56 boulevard exemple"),
    ("proprio2", "Terrain Hay Hassani 7", Categorie.FOOT_7, Zone.HAY_HASSANI, "380", "3 rue exemple"),
    ("proprio2", "Terrain Aïn Chock 7", Categorie.FOOT_7, Zone.AIN_CHOCK, "450", "17 avenue exemple"),
    ("proprio1", "Stade Sidi Maârouf", Categorie.FOOT_11, Zone.SIDI_MAAROUF, "500", "1 route exemple"),
    ("proprio1", "Stade Sidi Bernoussi", Categorie.FOOT_11, Zone.SIDI_BERNOUSSI, "650", "9 boulevard exemple"),
    ("proprio2", "Stade Hay Mohammadi", Categorie.FOOT_11, Zone.HAY_MOHAMMADI, "750", "44 rue exemple"),
    ("proprio2", "Stade Derb Sultan", Categorie.FOOT_11, Zone.DERB_SULTAN, "900", "2 place exemple"),
]


class Command(BaseCommand):
    help = "Charge le jeu de données de démonstration FootBook."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Supprime puis recrée les comptes de démonstration.")

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        noms = [c[0] for c in COMPTES]
        if reset:
            Reservation.objects.filter(terrain__proprietaire__username__in=noms).delete()
            Utilisateur.objects.filter(username__in=noms).delete()
        if Utilisateur.objects.filter(username__in=noms).exists():
            self.stdout.write("Les données de démonstration existent déjà (utilisez --reset pour les recréer).")
            return

        u = {}
        for username, prenom, nom, role in COMPTES:
            u[username] = Utilisateur.objects.create_user(
                username=username, email=f"{username}@footbook.test", password=MOT_DE_PASSE,
                first_name=prenom, last_name=nom, role=role,
            )
        t = {}
        for proprio, nom, categorie, zone, prix, adresse in TERRAINS:
            t[nom] = Terrain.objects.create(proprietaire=u[proprio], nom=nom, categorie=categorie,
                                            zone=zone, prix=Decimal(prix), adresse=adresse)

        aujourd_hui = timezone.localdate()
        demain = aujourd_hui + timedelta(days=1)
        # Une réservation du jour pour tester le scan, une de demain avec annonce, une passée validée.
        Reservation.objects.create(terrain=t["Terrain Maârif 5"], joueur=u["joueur1"], date=aujourd_hui, heure=time(22))
        r2 = Reservation.objects.create(terrain=t["Terrain Anfa 5"], joueur=u["joueur1"], date=demain, heure=time(19))
        annonce = Annonce.objects.create(reservation=r2, joueurs_manquants=2, description="Match détente, niveau moyen.")
        Participation.objects.create(annonce=annonce, joueur=u["joueur3"])
        Reservation.objects.create(terrain=t["Terrain Bourgogne 7"], joueur=u["joueur2"],
                                   date=demain + timedelta(days=1), heure=time(18))
        Reservation.objects.create(terrain=t["Terrain Anfa 5"], joueur=u["joueur2"], date=aujourd_hui - timedelta(days=2),
                                   heure=time(20), statut=Statut.VALIDEE, valide_le=timezone.now() - timedelta(days=2))
        u["joueur2"].matchs_joues = 1
        u["joueur2"].save(update_fields=["matchs_joues"])

        self.stdout.write(self.style.SUCCESS(
            f"{len(COMPTES)} comptes (mot de passe : {MOT_DE_PASSE}), {len(TERRAINS)} terrains, "
            "4 réservations et 1 annonce créés."
        ))
