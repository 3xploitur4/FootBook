from django.urls import path

from annonces.views import PublierAnnonceView

from . import views

urlpatterns = [
    path("", views.MesReservationsView.as_view(), name="mes_reservations"),
    path("<int:pk>/qr/", views.QRCodeView.as_view(), name="qr_code"),
    path("<int:pk>/annonce/", PublierAnnonceView.as_view(), name="publier_annonce"),
    path("recues/", views.ReservationsRecuesView.as_view(), name="reservations_recues"),
    path("valider/", views.ValiderQRView.as_view(), name="valider_qr"),
]
