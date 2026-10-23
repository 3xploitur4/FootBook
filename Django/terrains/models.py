"""Modèle Terrain (SCRUM-27, T02.1) : schéma SCRUM-49, listes SCRUM-51."""
from django.conf import settings
from django.db import models


class Categorie(models.TextChoices):
    FOOT_5 = "5V5", "Foot à 5"
    FOOT_7 = "7V7", "Foot à 7"
    FOOT_11 = "11V11", "Foot à 11"


# Nombre total de joueurs sur le terrain (SCRUM-51), utilisé pour borner les annonces (SCRUM-57, B3).
JOUEURS_PAR_CATEGORIE = {Categorie.FOOT_5: 10, Categorie.FOOT_7: 14, Categorie.FOOT_11: 22}


class Zone(models.TextChoices):
    MAARIF = "MAARIF", "Maârif"
    ANFA = "ANFA", "Anfa"
    AIN_DIAB = "AIN_DIAB", "Aïn Diab"
    CALIFORNIE = "CALIFORNIE", "Californie"
    BOURGOGNE = "BOURGOGNE", "Bourgogne"
    AIN_SEBAA = "AIN_SEBAA", "Aïn Sebaâ"
    HAY_HASSANI = "HAY_HASSANI", "Hay Hassani"
    AIN_CHOCK = "AIN_CHOCK", "Aïn Chock"
    SIDI_MAAROUF = "SIDI_MAAROUF", "Sidi Maârouf"
    SIDI_BERNOUSSI = "SIDI_BERNOUSSI", "Sidi Bernoussi"
    HAY_MOHAMMADI = "HAY_MOHAMMADI", "Hay Mohammadi"
    DERB_SULTAN = "DERB_SULTAN", "Derb Sultan"


class Terrain(models.Model):
    # R7 : supprimer un propriétaire supprime ses terrains.
    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="terrains",
        limit_choices_to={"role": "PROPRIETAIRE"},
        verbose_name="propriétaire",
    )
    nom = models.CharField(max_length=100)
    categorie = models.CharField("catégorie", max_length=5, choices=Categorie.choices)
    prix = models.DecimalField("prix (DH par heure)", max_digits=7, decimal_places=2)
    zone = models.CharField(max_length=30, choices=Zone.choices)
    adresse = models.CharField(max_length=255)

    class Meta:
        ordering = ["prix", "nom"]
        constraints = [
            # R5 : un propriétaire n'a pas deux terrains du même nom.
            models.UniqueConstraint(fields=["proprietaire", "nom"], name="nom_unique_par_proprietaire"),
            # R4 : le prix est strictement positif.
            models.CheckConstraint(condition=models.Q(prix__gt=0), name="prix_positif"),
        ]

    def __str__(self):
        return self.nom

    @property
    def nb_joueurs(self):
        return JOUEURS_PAR_CATEGORIE[self.categorie]
