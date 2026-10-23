from django import forms

from .models import Annonce


class AnnonceForm(forms.ModelForm):
    class Meta:
        model = Annonce
        fields = ("joueurs_manquants", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4, "placeholder": "Niveau, poste recherché…"})}

    def __init__(self, *args, maximum, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximum = maximum
        champ = self.fields["joueurs_manquants"]
        champ.widget.attrs.update(min=1, max=maximum)
        champ.help_text = f"Entre 1 et {maximum} joueurs."

    def clean_joueurs_manquants(self):
        n = self.cleaned_data["joueurs_manquants"]
        if not 1 <= n <= self.maximum:  # B3
            raise forms.ValidationError(f"Entre 1 et {self.maximum} joueurs pour cette catégorie.")
        return n
