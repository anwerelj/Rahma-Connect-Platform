"""
Vues pour le rôle ASSOCIATION.
Gestion des demandes, besoins, dons disponibles, stock et distribution.
"""

from django.contrib import messages
from django.shortcuts import redirect, render

from .. import data as db
from ..decorators import role_required
from ..forms import NeedForm
from ..models import Besoin, Categorie, Reservation


@role_required("association")
def donations_list(request):
    """Liste des dons disponibles à réserver."""
    donations = [d for d in db.all_donations(request) if d["statut"] == "DISPONIBLE"]
    cat = request.GET.get("categorie", "")
    q = request.GET.get("q", "").strip().lower()
    sort = request.GET.get("tri", "recent")
    if cat.isdigit():
        donations = [d for d in donations if d["categorie"] == int(cat)]
    if q:
        donations = [d for d in donations if q in d["titre"].lower() or q in d["description"].lower()]
    if sort == "distance":
        donations.sort(key=lambda d: d["distance_km"])
    else:
        donations.sort(key=lambda d: d["date_publication"], reverse=True)
    return render(request, "core/association/dons_liste.html", {
        "donations": donations, "categories": db.CATEGORIES,
        "selected_cat": cat, "q": request.GET.get("q", ""), "sort": sort,
    })


@role_required("association")
def asso_demandes(request):
    """Tableau de gestion des demandes d'aide."""
    reqs = db.all_requests(request)
    return render(request, "core/association/demandes.html", {
        "pending": [r for r in reqs if r["statut"] == "EN_ATTENTE"],
        "validated": [r for r in reqs if r["statut"] in ("VALIDE", "DON_TROUVE", "EN_LIVRAISON")],
        "closed": [r for r in reqs if r["statut"] in ("REFUSE", "RECU")],
    })


@role_required("association")
def asso_besoins(request):
    """Liste des besoins déclarés par l'association."""
    return render(request, "core/association/besoins.html", {"needs": db.all_needs(request)})


@role_required("association")
def asso_besoin_nouveau(request):
    """Formulaire pour déclarer un nouveau besoin."""
    form = NeedForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        Besoin.objects.create(
            categorie=Categorie.objects.get(pk=data["categorie"]),
            description=data["description"],
            quantite=data["quantite"],
            priorite=data["priorite"],
            localisation=data["localisation"],
        )
        messages.success(request, "Besoin enregistré.")
        return redirect("asso_besoins")
    return render(request, "core/association/besoin_form.html", {"form": form})


@role_required("association")
def asso_stock(request):
    """Gestion du stock de l'association."""
    return render(request, "core/association/stock.html", {"items": db.get_stock_items()})


@role_required("association")
def asso_distribution(request):
    """Tableau de distribution des dons."""
    donations = db.all_donations(request)
    confirmed_donations = set(
        Reservation.objects.filter(statut="CONFIRMEE").values_list("don_id", flat=True)
    )
    for donation in donations:
        donation["reservation_confirmee"] = donation["id"] in confirmed_donations
    board = [
        ("Réservés", "RESERVE"), ("Collectés", "COLLECTE"),
        ("Reçus", "RECU"), ("Distribués", "DISTRIBUE"),
    ]
    columns = [{"title": title, "code": code, "items": [d for d in donations if d["statut"] == code]} for title, code in board]
    return render(request, "core/association/distribution.html", {"columns": columns})
