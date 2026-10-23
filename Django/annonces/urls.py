from django.urls import path

from . import views

urlpatterns = [
    path("", views.AnnoncesView.as_view(), name="annonces"),
    path("<int:pk>/rejoindre/", views.RejoindreView.as_view(), name="rejoindre"),
]
