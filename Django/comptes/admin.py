from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "matchs_joues")
    list_filter = ("role", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("FootBook", {"fields": ("role", "matchs_joues")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("FootBook", {"fields": ("email", "role")}),)
