"""Formulaires d'inscription et de connexion (SCRUM-25, T01.2)."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Role, Utilisateur


class FormulaireInscription(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ("username", "first_name", "last_name", "email", "role")
        labels = {"username": "Nom d'utilisateur", "first_name": "Prénom", "last_name": "Nom", "role": "Je suis"}
        widgets = {"role": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prénom et nom obligatoires (SCRUM-49).
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True
        self.fields["role"].choices = Role.choices
        self.fields["username"].widget.attrs["placeholder"] = "ex. ali_foot"
        self.fields["email"].widget.attrs["placeholder"] = "nom@exemple.com"

    def clean_email(self):
        # R1, sans tenir compte des majuscules.
        email = self.cleaned_data["email"].strip().lower()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte utilise déjà cette adresse email.")
        return email


class FormulaireConnexion(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Nom d'utilisateur ou mot de passe incorrect.",
    }
