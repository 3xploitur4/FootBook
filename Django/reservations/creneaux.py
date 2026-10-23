"""Créneaux réservables (SCRUM-53) : 1 h, à l'heure pile, de 9:00 à 22:00, jusqu'à J+14."""
import secrets
from datetime import time, timedelta

from django.utils import timezone

OUVERTURE, FERMETURE = 9, 23  # premier début 9:00, dernier début 22:00
HORIZON_JOURS = 14
HEURES = [time(h) for h in range(OUVERTURE, FERMETURE)]


def dates_reservables():
    aujourd_hui = timezone.localdate()
    return [aujourd_hui + timedelta(days=i) for i in range(HORIZON_JOURS + 1)]


def creneaux_libres(terrain, jour):
    """Heures libres d'un terrain pour un jour ; un créneau déjà commencé n'est pas proposé (C5)."""
    maintenant = timezone.localtime()
    prises = set(terrain.reservations.filter(date=jour).values_list("heure", flat=True))
    return [
        h for h in HEURES
        if h not in prises and (jour > maintenant.date() or h.hour > maintenant.hour)
    ]


def generer_code():
    """Code du QR (SCRUM-34) : 22 caractères aléatoires, impossible à deviner."""
    return secrets.token_urlsafe(16)
