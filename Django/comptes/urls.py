from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("inscription/", views.InscriptionView.as_view(), name="inscription"),
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    # Django 5 n'accepte la déconnexion qu'en POST (règle A6).
    path("deconnexion/", LogoutView.as_view(), name="deconnexion"),
    path("espace/", views.EspaceView.as_view(), name="espace"),
]
