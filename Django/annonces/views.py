"""Publier, lister et rejoindre une annonce (sprint 3, US-10 et US-11)."""
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import FormView, ListView

from comptes.models import Role
from comptes.permissions import RoleRequisMixin
from reservations.models import Reservation, Statut

from .forms import AnnonceForm
from .models import Annonce, Participation


class PublierAnnonceView(RoleRequisMixin, FormView):
    """B1 et B2 : l'auteur d'une réservation confirmée et à venir, une annonce au plus."""

    role_requis = Role.JOUEUR
    form_class = AnnonceForm
    template_name = "annonces/publier.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == Role.JOUEUR:
            self.reservation = get_object_or_404(
                Reservation.objects.select_related("terrain"),
                pk=kwargs["pk"], joueur=request.user, statut=Statut.CONFIRMEE,
            )
            if not self.reservation.est_a_venir or hasattr(self.reservation, "annonce"):
                raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["maximum"] = self.reservation.terrain.nb_joueurs - 1  # B3 : 9, 13 ou 21
        return kwargs

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        contexte["reservation"] = self.reservation
        return contexte

    def form_valid(self, form):
        annonce = form.save(commit=False)
        annonce.reservation = self.reservation
        try:
            annonce.save()
        except IntegrityError:  # B1, en cas de double envoi
            raise Http404
        messages.success(self.request, "Annonce publiée.")
        return redirect("annonces")


class AnnoncesView(RoleRequisMixin, ListView):
    role_requis = Role.JOUEUR
    template_name = "annonces/liste.html"
    context_object_name = "annonces"

    def get_queryset(self):
        return Annonce.ouvertes()


def rejoindre(annonce, joueur):
    """Renvoie None si le joueur a rejoint, sinon le message de refus (SCRUM-57, B4 et B5)."""
    try:
        with transaction.atomic():
            # Décrément conditionnel : sûr même avec SQLite, deux joueurs ne dépassent jamais la limite.
            n = (Annonce.objects.filter(pk=annonce.pk, ouverte=True, joueurs_manquants__gt=0)
                 .update(joueurs_manquants=F("joueurs_manquants") - 1))
            if n == 0:
                return "Cette annonce est complète."
            Participation.objects.create(annonce=annonce, joueur=joueur)
            Annonce.objects.filter(pk=annonce.pk, joueurs_manquants=0).update(ouverte=False)
    except IntegrityError:
        return "Vous participez déjà à ce match."
    return None


class RejoindreView(RoleRequisMixin, View):
    role_requis = Role.JOUEUR
    http_method_names = ["post"]  # GET -> 405 (A6)

    def post(self, request, pk):
        annonce = get_object_or_404(Annonce.objects.select_related("reservation"), pk=pk)
        if annonce.reservation.joueur_id == request.user.pk:
            messages.error(request, "Vous ne pouvez pas rejoindre votre propre annonce.")
        elif not annonce.reservation.est_a_venir:
            messages.error(request, "Ce match est déjà passé.")
        else:
            refus = rejoindre(annonce, request.user)
            if refus:
                messages.error(request, refus)
            else:
                messages.success(request, f"Vous avez rejoint le match du {annonce.reservation.date:%d/%m} à {annonce.reservation.heure:%H:%M}.")
        return redirect("annonces")
