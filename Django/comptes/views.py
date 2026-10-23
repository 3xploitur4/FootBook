"""Pages des comptes : inscription, connexion, Mon espace, profil joueur."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView

from .forms import FormulaireConnexion, FormulaireInscription
from .models import Role, Utilisateur
from .permissions import RoleRequisMixin


class InscriptionView(CreateView):
    form_class = FormulaireInscription
    template_name = "comptes/inscription.html"
    success_url = reverse_lazy("espace")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("espace")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        utilisateur = form.save()
        login(self.request, utilisateur)
        messages.success(self.request, "Bienvenue sur FootBook, votre compte est créé.")
        return redirect(self.success_url)


class ConnexionView(LoginView):
    template_name = "comptes/connexion.html"
    authentication_form = FormulaireConnexion
    redirect_authenticated_user = True


class EspaceView(LoginRequiredMixin, TemplateView):
    template_name = "comptes/espace.html"


class ProfilJoueurView(RoleRequisMixin, DetailView):
    """Profil public d'un joueur (US-12, SCRUM-46 ; champs fixés par SCRUM-59)."""

    role_requis = Role.JOUEUR
    template_name = "comptes/profil.html"
    context_object_name = "joueur"

    def get_queryset(self):
        # Un compte propriétaire ou un identifiant inconnu donne une 404.
        return Utilisateur.objects.filter(role=Role.JOUEUR)

    def get_context_data(self, **kwargs):
        from annonces.models import Annonce

        contexte = super().get_context_data(**kwargs)
        contexte["annonces"] = [a for a in Annonce.ouvertes().filter(reservation__joueur=self.object)]
        return contexte
