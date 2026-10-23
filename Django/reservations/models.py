"""Modèle Reservation (SCRUM-32, T04.1)."""
from datetime import datetime, time

from django.conf import settings
from django.db import models
from django.utils import timezone

from .creneaux import generer_code


class Statut(models.TextChoices):
    CONFIRMEE = "CONFIRMEE", "Confirmée"
    VALIDEE = "VALIDEE", "Validée"


class Reservation(models.Model):
    # Un terrain réservé ne peut pas être supprimé (conséquence de R7, SCRUM-49).
    terrain = models.ForeignKey("terrains.Terrain", on_delete=models.PROTECT, related_name="reservations")
    joueur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    date = models.DateField()
    heure = models.TimeField()
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.CONFIRMEE)
    code = models.CharField(max_length=22, unique=True, default=generer_code, editable=False)
    valide_le = models.DateTimeField("validée le", null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "heure"]
        constraints = [
            # EF-03 : pas deux réservations du même terrain au même créneau.
            models.UniqueConstraint(fields=["terrain", "date", "heure"], name="creneau_unique"),
            models.CheckConstraint(
                condition=models.Q(heure__gte=time(9)) & models.Q(heure__lte=time(22)),
                name="heure_ouverture",
            ),
        ]

    def __str__(self):
        return f"{self.terrain} · {self.date:%d/%m/%Y} {self.heure:%H:%M}"

    @property
    def debut(self):
        return timezone.make_aware(datetime.combine(self.date, self.heure))

    @property
    def est_a_venir(self):
        return self.debut >= timezone.now()

    @property
    def heure_fin(self):
        return time((self.heure.hour + 1) % 24)
