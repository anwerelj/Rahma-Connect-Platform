
from datetime import date
from django import forms
from django.contrib.auth.hashers import check_password
from . import data as db
from .models import Utilisateur


def category_choices():
    """Returns list of categories for dropdowns."""
    return [(c["id"], c["nom"]) for c in db.CATEGORIES]


PRIORITY_CHOICES = [(code, label) for code, (label, _) in db.PRIORITY.items()]


class StyledForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class LoginForm(StyledForm):
    email = forms.EmailField(label="Adresse e-mail")
    mot_de_passe = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class RegisterForm(StyledForm):
    nom = forms.CharField(label="Nom complet ou de l'organisme", max_length=80)
    email = forms.EmailField(label="Adresse e-mail")
    telephone = forms.CharField(label="Téléphone", max_length=20)
    role = forms.ChoiceField(
        label="Je m'inscris comme",
        choices=[(k, v) for k, v in db.ROLES.items() if k != "admin"],
    )
    mot_de_passe = forms.CharField(label="Mot de passe", min_length=8, widget=forms.PasswordInput)
    confirmation = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        if data.get("mot_de_passe") != data.get("confirmation"):
            self.add_error("confirmation", "Les deux mots de passe ne sont pas identiques.")
        return data

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email


class ProfilForm(StyledForm):
    """Formulaire de modification du profil — commun à tous les rôles."""
    nom = forms.CharField(label="Nom complet", max_length=80)
    email = forms.EmailField(label="Adresse e-mail")
    telephone = forms.CharField(label="Téléphone", max_length=20, required=False)
    ville = forms.CharField(label="Ville", max_length=80, required=False)

    # Champs mot de passe facultatifs : on ne change que si l'utilisateur remplit
    mot_de_passe_actuel = forms.CharField(
        label="Mot de passe actuel",
        widget=forms.PasswordInput,
        required=False,
    )
    nouveau_mot_de_passe = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput,
        min_length=8,
        required=False,
    )
    confirmation_mot_de_passe = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput,
        required=False,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # On garde l'utilisateur pour valider l'e-mail unique et le mot de passe actuel
        self._user = user

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # Autoriser l'e-mail actuel, refuser un e-mail déjà pris par quelqu'un d'autre
        if self._user and email != self._user.email.lower():
            if Utilisateur.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email

    def clean(self):
        data = super().clean()
        nouveau = data.get("nouveau_mot_de_passe")
        confirmation = data.get("confirmation_mot_de_passe")
        actuel = data.get("mot_de_passe_actuel")

        # Si l'utilisateur veut changer son mot de passe
        if nouveau:
            if not actuel:
                self.add_error("mot_de_passe_actuel", "Entrez votre mot de passe actuel pour le modifier.")
            elif self._user and not check_password(actuel, self._user.password_hash):
                self.add_error("mot_de_passe_actuel", "Mot de passe actuel incorrect.")
            if nouveau != confirmation:
                self.add_error("confirmation_mot_de_passe", "Les deux nouveaux mots de passe ne correspondent pas.")
        return data


class DonationForm(StyledForm):
    categorie = forms.ChoiceField(label="Catégorie")
    titre = forms.CharField(label="Titre du don", max_length=80)
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={"rows": 3}))
    quantite = forms.IntegerField(label="Quantité", min_value=1, initial=1)
    etat = forms.ChoiceField(label="État", choices=[
        ("Neuf", "Neuf"),
        ("Très bon", "Très bon état"),
        ("Bon", "Bon état"),
        ("Usagé", "Usagé"),
        ("Frais", "Frais (alimentaire)"),
        ("Emballé", "Emballé (alimentaire)"),
    ])
    localisation = forms.CharField(label="Localisation (ville ou quartier)", max_length=80)
    date_limite = forms.DateField(
        label="Date limite d'utilisation (facultatif)",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].choices = category_choices()

    def clean_date_limite(self):
        value = self.cleaned_data.get("date_limite")
        if value and value < date.today():
            raise forms.ValidationError("La date limite ne peut pas être dans le passé.")
        return value


class HelpRequestForm(StyledForm):
    categorie = forms.ChoiceField(label="Type de ressource")
    titre = forms.CharField(label="Ressource souhaitée", max_length=80)
    description = forms.CharField(label="Détails", widget=forms.Textarea(attrs={"rows": 3}))
    quantite = forms.IntegerField(label="Quantité", min_value=1, initial=1)
    motif = forms.CharField(label="Motif de la demande", max_length=200)
    priorite = forms.ChoiceField(label="Urgence", choices=PRIORITY_CHOICES, initial="MOYENNE")
    localisation = forms.CharField(label="Votre ville ou quartier", max_length=80)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].choices = category_choices()


class NeedForm(StyledForm):
    """Formulaire pour qu'une association déclare un besoin."""
    categorie = forms.ChoiceField(label="Catégorie")
    description = forms.CharField(label="Description du besoin", max_length=200)
    quantite = forms.IntegerField(label="Quantité", min_value=1, initial=1)
    priorite = forms.ChoiceField(label="Priorité", choices=PRIORITY_CHOICES, initial="MOYENNE")
    localisation = forms.CharField(label="Lieu de livraison", max_length=80)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].choices = category_choices()


class MotDePasseOublieForm(StyledForm):
    """Formulaire pour demander la réinitialisation de mot de passe."""
    email = forms.EmailField(label="Votre adresse e-mail")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if not Utilisateur.objects.filter(email__iexact=email, actif=True).exists():
            raise forms.ValidationError("Aucun compte actif trouvé avec cette adresse e-mail.")
        return email


class ReinitialisationMotDePasseForm(StyledForm):
    """Formulaire pour saisir un nouveau mot de passe."""
    nouveau_mot_de_passe = forms.CharField(label="Nouveau mot de passe", min_length=8, widget=forms.PasswordInput)
    confirmation = forms.CharField(label="Confirmer le nouveau mot de passe", widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        if data.get("nouveau_mot_de_passe") != data.get("confirmation"):
            self.add_error("confirmation", "Les deux mots de passe ne correspondent pas.")
        return data
