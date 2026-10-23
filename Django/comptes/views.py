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
    """Tableau de bord : raccourcis et chiffres clés selon le rôle (US-01, US-09)."""

    template_name = "comptes/espace.html"

    def get_context_data(self, **kwargs):
        from django.utils import timezone

        from annonces.models import Annonce
        from reservations.models import Reservation, Statut

        contexte = super().get_context_data(**kwargs)
        user = self.request.user
        aujourd_hui = timezone.localdate()
        if user.est_joueur:
            a_venir = [r for r in Reservation.objects.filter(joueur=user, date__gte=aujourd_hui)
                       .select_related("terrain") if r.est_a_venir]
            contexte.update(prochaines=a_venir[:5], nb_a_venir=len(a_venir),
                            nb_annonces=Annonce.ouvertes().exclude(reservation__joueur=user).count())
        else:
            recues = Reservation.objects.filter(terrain__proprietaire=user).select_related("terrain", "joueur")
            contexte.update(
                nb_terrains=user.terrains.count(),
                du_jour=list(recues.filter(date=aujourd_hui)),
                nb_a_venir=sum(1 for r in recues.filter(date__gte=aujourd_hui) if r.est_a_venir),
                nb_validees=recues.filter(statut=Statut.VALIDEE).count(),
            )
        return contexte


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
