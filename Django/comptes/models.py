"""Modèle Utilisateur (SCRUM-24, T01.1) : schéma du rapport SCRUM-49."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    JOUEUR = "JOUEUR", "Joueur"
    PROPRIETAIRE = "PROPRIETAIRE", "Propriétaire"


class Utilisateur(AbstractUser):
    # R1 : un seul compte par adresse email.
    email = models.EmailField("email", unique=True)
    # R2 : le rôle vaut JOUEUR ou PROPRIETAIRE, choisi à l'inscription.
    role = models.CharField("rôle", max_length=12, choices=Role.choices, default=Role.JOUEUR)
    # R3 : jamais négatif ; augmenté à la validation d'un QR code (SCRUM-40).
    matchs_joues = models.PositiveIntegerField("matchs joués", default=0)

    class Meta:
        verbose_name = "utilisateur"
        constraints = [
            models.CheckConstraint(condition=models.Q(role__in=Role.values), name="role_valide"),
        ]

    @property
    def est_joueur(self):
        return self.role == Role.JOUEUR

    @property
    def est_proprietaire(self):
        return self.role == Role.PROPRIETAIRE

    @property
    def nom_affiche(self):
        return self.get_full_name() or self.username

    def __str__(self):
        return self.nom_affiche
