from datetime import date, time

from django import forms

from .creneaux import HEURES, creneaux_libres, dates_reservables


class ReservationForm(forms.Form):
    """Choix d'une date et d'un créneau (SCRUM-33). La base tranche les conflits (EF-03)."""

    date = forms.TypedChoiceField(coerce=date.fromisoformat)
    heure = forms.TypedChoiceField(coerce=time.fromisoformat, widget=forms.RadioSelect)

    def __init__(self, *args, terrain, **kwargs):
        super().__init__(*args, **kwargs)
        self.terrain = terrain
        self.fields["date"].choices = [(d.isoformat(), d.isoformat()) for d in dates_reservables()]
        self.fields["heure"].choices = [(h.strftime("%H:%M"), h.strftime("%H:%M")) for h in HEURES]
        self.fields["date"].error_messages["invalid_choice"] = "Choisissez une date entre aujourd'hui et J+14."
        self.fields["heure"].error_messages["invalid_choice"] = "Choisissez un créneau à l'heure pile, de 9:00 à 22:00."

    def clean(self):
        donnees = super().clean()
        jour, heure = donnees.get("date"), donnees.get("heure")
        if jour and heure and heure not in creneaux_libres(self.terrain, jour):
            raise forms.ValidationError("Ce créneau n'est plus disponible. Choisissez-en un autre.")
        return donnees


class ValidationForm(forms.Form):
    """Saisie ou scan du code (SCRUM-55, cas V1)."""

    code = forms.RegexField(
        regex=r"^[A-Za-z0-9_-]{22}$",
        label="Ou saisissez le code",
        error_messages={"invalid": "Code invalide.", "required": "Code invalide."},
        widget=forms.TextInput(attrs={"placeholder": "22 caractères", "autocomplete": "off"}),
    )

    def clean_code(self):
        return self.cleaned_data["code"].strip()
