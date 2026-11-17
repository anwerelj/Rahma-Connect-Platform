"""
Vues pour le rôle DONATEUR.
Gestion des dons et des réservations.
"""

from datetime import date
from uuid import uuid4
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

from .. import data as db
from ..decorators import role_required
from ..forms import DonationForm
from ..models import Categorie, Don, Reservation, Utilisateur


@role_required("donateur")
def mes_dons(request):
    """Liste des dons publiés par le donateur."""
    me = request.session["user"]["nom"]
    mine = [d for d in db.all_donations(request) if d["donateur"] == me]
    status = request.GET.get("statut", "")
    if status in db.DONATION_STATUS:
        mine = [d for d in mine if d["statut"] == status]
    return render(request, "core/donateur/mes_dons.html", {
        "donations": mine[::-1], "status_filter": status, "statuses": db.DONATION_STATUS,
    })


@role_required("donateur")
def don_nouveau(request):
    """Formulaire pour publier un nouveau don."""
    form = DonationForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        actor = Utilisateur.objects.filter(email=request.session["user"]["email"]).first()
        if actor is None:
            messages.error(request, "Votre session ne correspond plus à un utilisateur actif.")
        else:
            data = form.cleaned_data
            Don.objects.create(
                ref=f"DON-{uuid4().hex[:12].upper()}",
                titre=data["titre"],
                categorie=Categorie.objects.get(pk=data["categorie"]),
                description=data["description"],
                quantite=data["quantite"],
                etat=data["etat"],
                localisation=data["localisation"],
                donateur=actor,
                date_publication=date.today(),
                date_limite=data["date_limite"],
            )
            messages.success(request, "Votre don a été publié. Merci pour votre générosité !")
            return redirect("mes_dons")
    return render(request, "core/donateur/don_form.html", {"form": form})


@role_required("donateur")
def reservations(request):
    """Liste des réservations faites sur mes dons."""
    email = request.session["user"]["email"]
    items = Reservation.objects.filter(
        don__donateur__email=email,
    ).select_related("don", "association").order_by("-date", "-pk")
    return render(request, "core/donateur/reservations.html", {"items": items})


@role_required("donateur", "association", "logistique")
def donation_detail(request, pk):
    """Page de détail d'un don."""
    don = db.get_donation(request, pk)
    if don is None:
        raise Http404("Don introuvable")
    return render(request, "core/donateur/don_detail.html", {"don": don})
