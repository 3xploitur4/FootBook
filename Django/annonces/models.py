"""Modèles Annonce (SCRUM-42) et Participation (SCRUM-44) ; règles B1 à B7 de SCRUM-57."""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Annonce(models.Model):
    # B1 : une seule annonce par réservation.
    reservation = models.OneToOneField("reservations.Reservation", on_delete=models.CASCADE, related_name="annonce")
    joueurs_manquants = models.PositiveSmallIntegerField("joueurs manquants")
    description = models.TextField(blank=True)
    ouverte = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["reservation__date", "reservation__heure"]

    def __str__(self):
        return f"Annonce · {self.reservation}"

    @property
    def auteur(self):
        return self.reservation.joueur

    @property
    def ids_participants(self):
        return [p.joueur_id for p in self.participations.all()]

    @classmethod
    def ouvertes(cls):
        """Annonces ouvertes dont le match n'est pas encore commencé (B6)."""
        maintenant = timezone.localtime()
        qs = (cls.objects.filter(ouverte=True, joueurs_manquants__gt=0, reservation__date__gte=maintenant.date())
              .select_related("reservation__terrain", "reservation__joueur")
              .prefetch_related("participations__joueur"))
        # Le jour même, seules les heures à venir restent.
        return qs.exclude(reservation__date=maintenant.date(), reservation__heure__lte=maintenant.time())


class Participation(models.Model):
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name="participations")
    joueur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="participations")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["cree_le"]
        constraints = [
            # Pas de double participation (US-11).
            models.UniqueConstraint(fields=["annonce", "joueur"], name="participation_unique"),
        ]

    def __str__(self):
        return f"{self.joueur} → {self.annonce}"
