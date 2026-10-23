"""Formulaires des terrains : ajout / modification (SCRUM-28) et filtres (SCRUM-31)."""
from django import forms

from .models import Categorie, Terrain, Zone


class TerrainForm(forms.ModelForm):
    """Le propriétaire n'est pas un champ : la vue l'impose (R6)."""

    class Meta:
        model = Terrain
        fields = ("nom", "categorie", "zone", "prix", "adresse")
        widgets = {"prix": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "placeholder": "0.00"})}

    def __init__(self, *args, proprietaire, **kwargs):
        super().__init__(*args, **kwargs)
        self.proprietaire = proprietaire

    def clean_nom(self):
        # R5 : Django ne vérifie pas seul l'unicité (proprietaire, nom), car proprietaire
        # n'est pas dans le formulaire (point d'implémentation de SCRUM-66).
        nom = self.cleaned_data["nom"].strip()
        doublons = Terrain.objects.filter(proprietaire=self.proprietaire, nom__iexact=nom)
        if self.instance.pk:
            doublons = doublons.exclude(pk=self.instance.pk)
        if doublons.exists():
            raise forms.ValidationError("Vous avez déjà un terrain portant ce nom.")
        return nom

    def clean_prix(self):
        prix = self.cleaned_data["prix"]
        if prix is None or prix <= 0:  # R4
            raise forms.ValidationError("Le prix doit être strictement positif.")
        return prix


TOUTES = [("", "Toutes")]


class FiltreTerrainForm(forms.Form):
    """Filtres de recherche (SCRUM-51) : tous facultatifs, combinés par un ET."""

    categorie = forms.ChoiceField(label="Catégorie", choices=TOUTES + Categorie.choices, required=False)
    zone = forms.ChoiceField(choices=TOUTES + Zone.choices, required=False)
    prix_min = forms.DecimalField(label="Prix min (DH/h)", min_value=0, max_digits=7, decimal_places=2, required=False)
    prix_max = forms.DecimalField(label="Prix max (DH/h)", min_value=0, max_digits=7, decimal_places=2, required=False)

    def clean(self):
        donnees = super().clean()
        mini, maxi = donnees.get("prix_min"), donnees.get("prix_max")
        if mini is not None and maxi is not None and mini > maxi:
            raise forms.ValidationError("Le prix minimum dépasse le prix maximum.")
        return donnees
