from django.urls import path

from reservations.views import ReserverView

from . import views

urlpatterns = [
    path("", views.ListeTerrainsView.as_view(), name="terrains"),
    path("mes-terrains/", views.MesTerrainsView.as_view(), name="mes_terrains"),
    path("ajouter/", views.AjouterTerrainView.as_view(), name="ajouter_terrain"),
    path("<int:pk>/modifier/", views.ModifierTerrainView.as_view(), name="modifier_terrain"),
    path("<int:pk>/supprimer/", views.SupprimerTerrainView.as_view(), name="supprimer_terrain"),
    path("<int:pk>/reserver/", ReserverView.as_view(), name="reserver"),
]
