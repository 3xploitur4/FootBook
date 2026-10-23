"""Restriction des pages par rôle (SCRUM-26, T01.3 ; règles A1 et A2 de SCRUM-50).

Visiteur -> redirection vers la connexion ; connecté du mauvais rôle -> 403.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequisMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Réserve une vue à un rôle : 'JOUEUR' ou 'PROPRIETAIRE'."""

    role_requis = None

    def test_func(self):
        return self.request.user.role == self.role_requis
