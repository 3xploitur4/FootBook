from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="accueil.html"), name="accueil"),
    path("admin/", admin.site.urls),
    path("comptes/", include("comptes.urls")),
    path("joueurs/", include("comptes.urls_profil")),
    path("terrains/", include("terrains.urls")),
    path("reservations/", include("reservations.urls")),
    path("annonces/", include("annonces.urls")),
]
