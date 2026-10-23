"""Réservation, QR code, validation et listes de réservations (sprint 2)."""
from datetime import date

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from comptes.models import Role, Utilisateur
from comptes.permissions import RoleRequisMixin
from terrains.models import Terrain

from .creneaux import creneaux_libres, dates_reservables
from .forms import ReservationForm, ValidationForm
from .models import Reservation, Statut


class ReserverView(RoleRequisMixin, FormView):
    """Réserver un créneau (US-04, SCRUM-33)."""

    role_requis = Role.JOUEUR
    form_class = ReservationForm
    template_name = "reservations/reserver.html"

    def dispatch(self, request, *args, **kwargs):
        self.terrain = get_object_or_404(Terrain, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["terrain"] = self.terrain
        return kwargs

    def jour_choisi(self):
        valeur = self.request.POST.get("date") or self.request.GET.get("date")
        dates = dates_reservables()
        try:
            jour = date.fromisoformat(valeur) if valeur else dates[0]
        except ValueError:
            jour = dates[0]
        return jour if jour in dates else dates[0]

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        jour = self.jour_choisi()
        contexte.update(terrain=self.terrain, dates=dates_reservables(), jour=jour,
                        creneaux=creneaux_libres(self.terrain, jour))
        return contexte

    def form_valid(self, form):
        try:
            with transaction.atomic():
                reservation = Reservation.objects.create(
                    terrain=self.terrain,
                    joueur=self.request.user,  # le joueur n'est pas un champ du formulaire
                    date=form.cleaned_data["date"],
                    heure=form.cleaned_data["heure"],
                )
        except IntegrityError:
            # Deux joueurs ont envoyé le même créneau : la contrainte d'unicité a tranché.
            form.add_error(None, "Ce créneau vient d'être réservé par un autre joueur. Choisissez-en un autre.")
            return self.form_invalid(form)
        messages.success(self.request, "Réservation confirmée.")
        return redirect("qr_code", pk=reservation.pk)


def qr_svg(code):
    image = qrcode.make(code, image_factory=qrcode.image.svg.SvgPathImage, box_size=12, border=2)
    return mark_safe(image.to_string(encoding="unicode"))


class QRCodeView(RoleRequisMixin, DetailView):
    """QR code d'une réservation, visible du seul joueur concerné (US-05, A3)."""

    role_requis = Role.JOUEUR
    template_name = "reservations/qr_code.html"
    context_object_name = "reservation"

    def get_queryset(self):
        return Reservation.objects.filter(joueur=self.request.user).select_related("terrain")

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        contexte["qr"] = qr_svg(self.object.code)
        return contexte


class MesReservationsView(RoleRequisMixin, ListView):
    """Historique du joueur, à venir et passées (US-08, SCRUM-39)."""

    role_requis = Role.JOUEUR
    template_name = "reservations/mes_reservations.html"

    def get_queryset(self):
        return (Reservation.objects.filter(joueur=self.request.user)
                .select_related("terrain", "annonce"))

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        reservations = list(self.object_list)
        contexte["a_venir"] = [r for r in reservations if r.est_a_venir]
        contexte["passees"] = sorted([r for r in reservations if not r.est_a_venir], key=lambda r: r.debut, reverse=True)
        return contexte


class ReservationsRecuesView(RoleRequisMixin, ListView):
    """Réservations des terrains du propriétaire (US-07, SCRUM-38, A4)."""

    role_requis = Role.PROPRIETAIRE
    template_name = "reservations/recues.html"

    def get_queryset(self):
        return (Reservation.objects.filter(terrain__proprietaire=self.request.user)
                .select_related("terrain", "joueur"))

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        reservations = list(self.object_list)
        contexte["a_venir"] = [r for r in reservations if r.est_a_venir]
        contexte["passees"] = sorted([r for r in reservations if not r.est_a_venir], key=lambda r: r.debut, reverse=True)
        return contexte


class ValiderQRView(RoleRequisMixin, View):
    """Valider un QR code (US-06, SCRUM-36/37) ; cas d'erreur V1 à V4 de SCRUM-55."""

    role_requis = Role.PROPRIETAIRE
    template_name = "reservations/valider.html"

    def get(self, request):
        return render(request, self.template_name, {"form": ValidationForm()})

    def afficher(self, form, erreur=None, reservation=None, succes=False):
        return render(self.request, self.template_name,
                      {"form": form, "erreur": erreur, "reservation": reservation, "succes": succes})

    def post(self, request):
        form = ValidationForm(request.POST)
        if not form.is_valid():  # V1
            return self.afficher(form, "Code invalide.")
        r = (Reservation.objects.select_related("terrain", "joueur")
             .filter(code=form.cleaned_data["code"], terrain__proprietaire=request.user).first())
        if r is None:  # V2 : code inconnu ou terrain d'un autre propriétaire, même message
            return self.afficher(form, "Aucune réservation ne correspond à ce code pour vos terrains.")
        if r.statut == Statut.VALIDEE:  # V3
            moment = timezone.localtime(r.valide_le)
            return self.afficher(form, f"Réservation déjà validée le {moment:%d/%m/%Y} à {moment:%H:%M}.", r)
        if r.date != timezone.localdate():  # V4
            return self.afficher(form, f"Cette réservation est prévue le {r.date:%d/%m/%Y} à {r.heure:%H:%M}.", r)
        with transaction.atomic():
            # Mise à jour conditionnelle : sûre même avec SQLite, qui ignore select_for_update (ENF-04).
            n = (Reservation.objects.filter(pk=r.pk, statut=Statut.CONFIRMEE)
                 .update(statut=Statut.VALIDEE, valide_le=timezone.now()))
            if n == 0:  # scan simultané
                return self.afficher(form, "Réservation déjà validée.", r)
            # T09.1 (SCRUM-40) : matchs_joues + 1 pour l'auteur et les participants (SCRUM-57, B7).
            ids = [r.joueur_id]
            if hasattr(r, "annonce"):
                ids += list(r.annonce.participations.values_list("joueur_id", flat=True))
            Utilisateur.objects.filter(pk__in=ids).update(matchs_joues=F("matchs_joues") + 1)
        r.refresh_from_db()
        return self.afficher(ValidationForm(), reservation=r, succes=True)
