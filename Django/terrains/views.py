"""Pages des terrains : recherche (joueur) et gestion (propriétaire)."""
from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from comptes.models import Role
from comptes.permissions import RoleRequisMixin

from .forms import FiltreTerrainForm, TerrainForm
from .models import Terrain


class ListeTerrainsView(RoleRequisMixin, ListView):
    """Liste et filtres (US-03, SCRUM-30 et SCRUM-31)."""

    role_requis = Role.JOUEUR
    model = Terrain
    template_name = "terrains/liste.html"
    context_object_name = "terrains"

    def get_queryset(self):
        terrains = super().get_queryset()
        self.form = FiltreTerrainForm(self.request.GET or None)
        if self.request.GET and self.form.is_valid():
            d = self.form.cleaned_data
            if d["categorie"]:
                terrains = terrains.filter(categorie=d["categorie"])
            if d["zone"]:
                terrains = terrains.filter(zone=d["zone"])
            if d["prix_min"] is not None:
                terrains = terrains.filter(prix__gte=d["prix_min"])
            if d["prix_max"] is not None:
                terrains = terrains.filter(prix__lte=d["prix_max"])
        # Formulaire invalide : liste complète, erreurs affichées dans le gabarit.
        return terrains.order_by("prix", "nom")

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        contexte["form"] = self.form
        return contexte


class ProprietaireMixin(RoleRequisMixin):
    role_requis = Role.PROPRIETAIRE

    def get_queryset(self):
        # A4 : un propriétaire ne voit et ne modifie que ses terrains (sinon 404).
        return Terrain.objects.filter(proprietaire=self.request.user)


class MesTerrainsView(ProprietaireMixin, ListView):
    template_name = "terrains/mes_terrains.html"
    context_object_name = "terrains"


class FormulaireTerrainMixin(ProprietaireMixin):
    form_class = TerrainForm
    template_name = "terrains/formulaire.html"
    success_url = reverse_lazy("mes_terrains")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["proprietaire"] = self.request.user
        return kwargs


class AjouterTerrainView(FormulaireTerrainMixin, CreateView):
    def form_valid(self, form):
        terrain = form.save(commit=False)
        terrain.proprietaire = self.request.user  # R6 : imposé par la vue
        terrain.save()
        messages.success(self.request, f"Le terrain « {terrain.nom} » est ajouté.")
        return redirect(self.success_url)


class ModifierTerrainView(FormulaireTerrainMixin, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, "Le terrain est modifié.")
        return super().form_valid(form)


class SupprimerTerrainView(ProprietaireMixin, DeleteView):
    template_name = "terrains/supprimer.html"
    success_url = reverse_lazy("mes_terrains")

    def form_valid(self, form):
        nom = self.object.nom
        try:
            self.object.delete()
        except ProtectedError:
            # Conséquence de R7 (SCRUM-49) : un terrain réservé ne peut pas être supprimé.
            messages.error(self.request, f"« {nom} » a des réservations : il ne peut pas être supprimé.")
            return redirect(self.success_url)
        messages.success(self.request, f"Le terrain « {nom} » est supprimé.")
        return redirect(self.success_url)
