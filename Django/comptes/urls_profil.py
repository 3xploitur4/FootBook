from django.urls import path

from . import views

urlpatterns = [
    path("<int:pk>/", views.ProfilJoueurView.as_view(), name="profil_joueur"),
]
