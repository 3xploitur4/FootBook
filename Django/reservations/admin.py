from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("terrain", "joueur", "date", "heure", "statut", "valide_le")
    list_filter = ("statut", "date")
    readonly_fields = ("code", "valide_le", "cree_le")
