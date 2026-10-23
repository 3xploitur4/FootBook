from django.contrib import admin

from .models import Terrain


@admin.register(Terrain)
class TerrainAdmin(admin.ModelAdmin):
    list_display = ("nom", "proprietaire", "categorie", "zone", "prix")
    list_filter = ("categorie", "zone")
    search_fields = ("nom", "adresse")
