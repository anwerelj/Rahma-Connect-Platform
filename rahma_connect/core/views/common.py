"""
Vues communes à tous les rôles.
Pages publiques et actions partagées.
"""

from datetime import date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .. import data as db
from ..decorators import login_required, role_required
from ..forms import (
    LoginForm,
    RegisterForm,
    ProfilForm,
    MotDePasseOublieForm,
    ReinitialisationMotDePasseForm,
)
from ..models import Besoin, DemandeAide, Don, Mission, Reservation, Utilisateur


def _send_email_safe(subject, message, recipients):
    """Envoie un e-mail via Mailtrap en capturant les erreurs éventuelles."""
    if not settings.EMAIL_HOST_USER:
        print(f"[MAILTRAP SIMULÉ] Vers: {recipients} | Sujet: {subject}")
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        print(f"[MAILTRAP SUCCÈS] Vers: {recipients} | Sujet: {subject}")
    except Exception as e:
        print(f"[MAILTRAP ERREUR] {e}")


def _send_password_reset_email(user, reset_url):
    subject = "[Rahma Connect] Réinitialisation de votre mot de passe"
    message = (
        f"Bonjour {user.nom},\n\n"
        f"Cliquez sur ce lien pour réinitialiser votre mot de passe (valable 24h) :\n"
        f"{reset_url}\n\n"
        f"Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail.\n\n"
        f"Cordialement,\nL'équipe Rahma Connect"
    )
    _send_email_safe(subject, message, [user.email])


def _send_reservation_notification(reservation):
    don = reservation.don
    subject = f"[Rahma Connect] Don réservé : {don.titre}"
    message = (
        f"Bonjour {don.donateur.nom},\n\n"
        f"L'association « {reservation.association.nom} » a réservé votre don « {don.titre} » ({reservation.quantite} unité(s)).\n"
        f"Connectez-vous pour accepter ou refuser la réservation.\n\n"
        f"Cordialement,\nL'équipe Rahma Connect"
    )
    _send_email_safe(subject, message, [don.donateur.email])


def _send_reservation_status_notification(reservation):
    statut = "acceptée" if reservation.statut == "CONFIRMEE" else "refusée"
    subject = f"[Rahma Connect] Réservation {statut}"
    message = (
        f"Bonjour {reservation.association.nom},\n\n"
        f"Le donateur a {statut} votre réservation pour le don « {reservation.don.titre} ».\n\n"
        f"Cordialement,\nL'équipe Rahma Connect"
    )
    _send_email_safe(subject, message, [reservation.association.email])


def home(request):
    """Redirige vers le dashboard si connecté, sinon vers la page de connexion."""
    if request.session.get("role"):
        return redirect("dashboard")
    return redirect("login")


def login_view(request):
    """Page de connexion.
    Si l'utilisateur est déjà connecté, on le redirige vers le dashboard.
    """
    if request.session.get("role"):
        return redirect("dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["mot_de_passe"]
        user = Utilisateur.objects.filter(email__iexact=email, actif=True).first()
        if user is not None and check_password(password, user.password_hash):
            _start_session(request, user)
            return redirect("dashboard")
        form.add_error(None, "Adresse e-mail ou mot de passe incorrect.")
    return render(request, "core/common/login.html", {"form": form})


def register_view(request):
    """Page d'inscription."""
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        user = Utilisateur.objects.create(
            nom=data["nom"],
            email=data["email"],
            telephone=data["telephone"],
            ville="",
            role=data["role"],
            password_hash=make_password(data["mot_de_passe"]),
            date_inscription=date.today(),
        )
        _start_session(request, user)
        messages.success(request, f"Bienvenue {data['nom']} !")
        return redirect("dashboard")
    return render(request, "core/common/register.html", {"form": form})


def mot_de_passe_oublie(request):
    """Demande de réinitialisation de mot de passe avec envoi d'e-mail via Mailtrap."""
    if request.session.get("role"):
        return redirect("dashboard")
    form = MotDePasseOublieForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        user = Utilisateur.objects.get(email__iexact=email, actif=True)
        # Génération d'un token sécurisé signé avec horodatage (valide 24 heures)
        token = signing.dumps({"email": user.email}, salt="pwd-reset")
        lien = request.build_absolute_uri(reverse("reinitialiser_mot_de_passe", args=[token]))
        _send_password_reset_email(user, lien)
        messages.success(
            request,
            "Un e-mail de réinitialisation vous a été envoyé. Vérifiez votre boîte Mailtrap !"
        )
        return redirect("login")
    return render(request, "core/common/mot_de_passe_oublie.html", {"form": form})


def reinitialiser_mot_de_passe(request, token):
    """Page de saisie du nouveau mot de passe après validation du token reçu."""
    if request.session.get("role"):
        return redirect("dashboard")
    try:
        data = signing.loads(token, salt="pwd-reset", max_age=86400)
        email = data.get("email")
        user = Utilisateur.objects.get(email__iexact=email, actif=True)
    except (signing.BadSignature, signing.SignatureExpired, Utilisateur.DoesNotExist):
        messages.error(request, "Ce lien de réinitialisation est invalide ou a expiré.")
        return redirect("mot_de_passe_oublie")

    form = ReinitialisationMotDePasseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user.password_hash = make_password(form.cleaned_data["nouveau_mot_de_passe"])
        user.save(update_fields=["password_hash"])
        messages.success(
            request,
            "Votre mot de passe a été modifié avec succès. Vous pouvez maintenant vous connecter."
        )
        return redirect("login")

    return render(request, "core/common/mot_de_passe_reinit.html", {"form": form})


def logout_view(request):
    """Déconnexion."""
    request.session.flush()
    return redirect("home")


def _start_session(request, user):
    """Initialise la session pour un utilisateur."""
    request.session.flush()
    request.session["role"] = user.role
    request.session["user"] = {
        "nom": user.nom,
        "email": user.email,
        "telephone": user.telephone,
        "ville": user.ville,
        "type": user.get_role_display(),
    }


@login_required
def dashboard(request):
    """Tableau de bord adapté au rôle de l'utilisateur."""
    role = request.session["role"]
    me = request.session["user"]["nom"]
    donations = db.all_donations(request)
    reqs = db.all_requests(request)
    ctx = {}

    if role == "donateur":
        mine = [d for d in donations if d["donateur"] == me]
        ctx["stats"] = [
            {"label": "Mes dons", "value": len(mine)},
            {"label": "Dons distribués", "value": sum(1 for d in mine if d["statut"] == "DISTRIBUE")},
        ]
        ctx["recent"] = mine[::-1][:5]

    elif role == "beneficiaire":
        mine = [r for r in reqs if r["beneficiaire"] == me]
        ctx["stats"] = [
            {"label": "Mes demandes", "value": len(mine)},
            {"label": "Aides reçues", "value": sum(1 for r in mine if r["statut"] == "RECU")},
        ]
        ctx["recent"] = mine[::-1][:5]

    elif role == "association":
        stock = db.get_stock_items()
        ctx["stats"] = [
            {"label": "Demandes en attente", "value": sum(1 for r in reqs if r["statut"] == "EN_ATTENTE")},
            {"label": "Stocks faibles", "value": sum(1 for s in stock if s["faible"])},
        ]
        ctx["pending"] = [r for r in reqs if r["statut"] == "EN_ATTENTE"]
        ctx["available"] = [d for d in donations if d["statut"] == "DISPONIBLE"][:4]

    elif role == "logistique":
        missions = db.all_missions(request)
        mine = [m for m in missions if m["livreur"] == me]
        ctx["stats"] = [
            {"label": "Mes missions", "value": len(mine)},
            {"label": "Terminées", "value": sum(1 for m in mine if m["statut"] == "LIVRE")},
        ]
        ctx["recent"] = [m for m in mine if m["statut"] != "LIVRE"]
        ctx["open_missions"] = [m for m in missions if m["livreur"] is None]

    elif role == "admin":
        ctx["stats"] = [
            {"label": "Utilisateurs", "value": Utilisateur.objects.count()},
            {"label": "Demandes en attente", "value": sum(1 for r in reqs if r["statut"] == "EN_ATTENTE")},
        ]
        ctx["urgent"] = [r for r in reqs if r["priorite"] == "URGENTE" and r["statut"] in ("EN_ATTENTE", "VALIDE")]

    return render(request, f"core/{role}/dashboard.html", ctx)


@login_required
def profil(request):
    """Page de profil — affichage et modification pour tous les rôles."""
    actor = Utilisateur.objects.filter(email=request.session["user"]["email"]).first()
    if actor is None:
        return redirect("logout")

    # Pré-remplir le formulaire avec les données actuelles
    initial = {
        "nom": actor.nom,
        "email": actor.email,
        "telephone": actor.telephone,
        "ville": actor.ville,
    }
    form = ProfilForm(request.POST or None, user=actor, initial=initial)

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        actor.nom = data["nom"]
        actor.email = data["email"]
        actor.telephone = data["telephone"]
        actor.ville = data["ville"]

        # Changer le mot de passe seulement si l'utilisateur a rempli le champ
        if data.get("nouveau_mot_de_passe"):
            from django.contrib.auth.hashers import make_password
            actor.password_hash = make_password(data["nouveau_mot_de_passe"])
            actor.save(update_fields=["nom", "email", "telephone", "ville", "password_hash"])
        else:
            actor.save(update_fields=["nom", "email", "telephone", "ville"])

        # Mettre à jour la session avec les nouvelles infos
        _start_session(request, actor)
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect("profil")

    return render(request, "core/common/profil.html", {"form": form})


# Actions autorisées par rôle
ALLOWED_ACTIONS = {
    ("request", "VALIDE"): {"association"},
    ("request", "REFUSE"): {"association"},
    ("request", "RECU"): {"beneficiaire"},
    ("donation", "RESERVE"): {"association"},
    ("donation", "COLLECTE"): {"donateur", "logistique"},
    ("donation", "RECU"): {"association"},
    ("donation", "DISTRIBUE"): {"association"},
    ("donation", "ANNULE"): {"donateur"},
    ("reservation", "CONFIRMEE"): {"donateur"},
    ("reservation", "REFUSEE"): {"donateur"},
    ("mission", "CREE"): {"association"},
}

NEXT_STEP = {
    "CREE": ("ACCEPTE", "Accepter la mission"),
    "ACCEPTE": ("EN_ROUTE", "Je pars vers le point de collecte"),
    "EN_ROUTE": ("RECUPERE", "Confirmer la récupération du don"),
    "RECUPERE": ("EN_LIVRAISON", "Démarrer la livraison"),
    "EN_LIVRAISON": ("LIVRE", "Confirmer la livraison"),
}


@require_POST
@login_required
def change_status(request):
    """Point d'entrée unique pour tous les changements de statut."""
    kind = request.POST.get("kind", "")
    code = request.POST.get("code", "")
    try:
        pk = int(request.POST.get("pk", ""))
    except ValueError:
        raise Http404("Identifiant invalide")
    role = request.session["role"]

    if kind == "delivery":
        allowed = {"logistique"} if code in db.STEPS["delivery"] else set()
    else:
        allowed = ALLOWED_ACTIONS.get((kind, code), set())

    if role != "admin" and role not in allowed:
        messages.error(request, "Action non autorisée pour votre rôle.")
    else:
        actor = Utilisateur.objects.filter(email=request.session["user"]["email"]).first()
        if actor is None:
            messages.error(request, "Votre session ne correspond plus à un utilisateur actif.")
        else:
            changed = _apply_status_change(kind, code, pk, role, actor)
            if changed:
                messages.success(request, "Statut mis à jour.")
            else:
                messages.error(request, "Cette action n'est plus disponible pour cet élément.")

    target = request.POST.get("next", "/")
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        target = "/"
    return redirect(target)


@transaction.atomic
def _apply_status_change(kind, code, pk, role, actor):
    """Applique un changement de statut de façon atomique."""
    is_admin = role == "admin"

    if kind == "request":
        try:
            item = DemandeAide.objects.select_for_update().get(pk=pk)
        except DemandeAide.DoesNotExist:
            raise Http404("Demande introuvable")

        transitions = {
            ("EN_ATTENTE", "VALIDE"): {"association"},
            ("EN_ATTENTE", "REFUSE"): {"association"},
            ("EN_LIVRAISON", "RECU"): {"beneficiaire"},
        }
        permitted_roles = transitions.get((item.statut, code), set())
        if not is_admin and role not in permitted_roles:
            return False
        if code == "RECU" and not is_admin and item.beneficiaire_id != actor.id:
            return False
        item.statut = code
        item.save(update_fields=["statut"])
        return True

    if kind == "donation":
        try:
            item = Don.objects.select_for_update().get(pk=pk)
        except Don.DoesNotExist:
            raise Http404("Don introuvable")

        transitions = {
            ("DISPONIBLE", "RESERVE"): "association",
            ("RESERVE", "COLLECTE"): "donateur",
            ("COLLECTE", "RECU"): "association",
            ("RECU", "DISTRIBUE"): "association",
            ("DISPONIBLE", "ANNULE"): "donateur",
        }
        expected_role = transitions.get((item.statut, code))
        if expected_role is None or (not is_admin and role != expected_role):
            return False
        if not is_admin and expected_role == "donateur" and item.donateur_id != actor.id:
            return False

        if code == "RESERVE":
            res = Reservation.objects.create(
                don=item,
                association=actor,
                quantite=item.quantite,
            )
            _send_reservation_notification(res)

        item.statut = code
        item.save(update_fields=["statut"])
        return True

    if kind == "reservation":
        try:
            item = Reservation.objects.select_for_update().select_related("don", "association", "don__donateur").get(pk=pk)
        except Reservation.DoesNotExist:
            raise Http404("Réservation introuvable")
        if (
            item.statut != "EN_ATTENTE"
            or item.don.statut != "RESERVE"
            or code not in ("CONFIRMEE", "REFUSEE")
            or (not is_admin and item.don.donateur_id != actor.id)
        ):
            return False
        item.statut = code
        item.save(update_fields=["statut"])
        if code == "REFUSEE":
            item.don.statut = "DISPONIBLE"
            item.don.save(update_fields=["statut"])
        _send_reservation_status_notification(item)
        return True

    if kind == "mission" and code == "CREE":
        try:
            don = Don.objects.select_for_update().get(pk=pk)
        except Don.DoesNotExist:
            raise Http404("Don introuvable")
        reservation = Reservation.objects.filter(
            don=don,
            statut="CONFIRMEE",
        ).order_by("-date", "-pk").first()
        if (
            don.statut != "RESERVE"
            or reservation is None
            or (not is_admin and reservation.association_id != actor.id)
            or Mission.objects.filter(don=don).exists()
        ):
            return False
        Mission.objects.create(
            don=don,
            point_collecte=don.localisation,
            point_livraison=reservation.association.ville or don.localisation,
            distance_km=don.distance_km,
            type_livreur="À attribuer",
            date_creation=date.today(),
        )
        return True

    if kind == "delivery":
        try:
            item = Mission.objects.select_for_update().select_related("don").get(pk=pk)
        except Mission.DoesNotExist:
            raise Http404("Mission introuvable")
        next_step = NEXT_STEP.get(item.statut)
        if (
            next_step is None
            or code != next_step[0]
            or (not is_admin and role != "logistique")
            or (not is_admin and item.livreur_id not in (None, actor.id))
        ):
            return False
        if item.livreur_id is None:
            item.livreur = actor
        item.statut = code
        item.save(update_fields=["statut", "livreur"])
        if code == "RECUPERE":
            item.don.statut = "COLLECTE"
            item.don.save(update_fields=["statut"])
        elif code == "LIVRE":
            item.don.statut = "RECU"
            item.don.save(update_fields=["statut"])
        return True

    return False
