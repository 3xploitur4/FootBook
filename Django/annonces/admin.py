from django.contrib import admin

from .models import Annonce, Participation


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 0


@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ("reservation", "joueurs_manquants", "ouverte")
    list_filter = ("ouverte",)
    inlines = [ParticipationInline]
