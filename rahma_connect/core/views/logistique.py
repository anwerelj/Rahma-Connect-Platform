"""
Vues pour le rôle PARTENAIRE LOGISTIQUE.
Gestion des missions de livraison.
"""

from django.http import Http404
from django.shortcuts import render

from .. import data as db
from ..decorators import role_required

# Étapes de progression des missions
NEXT_STEP = {
    "CREE": ("ACCEPTE", "Accepter la mission"),
    "ACCEPTE": ("EN_ROUTE", "Je pars vers le point de collecte"),
    "EN_ROUTE": ("RECUPERE", "Confirmer la récupération du don"),
    "RECUPERE": ("EN_LIVRAISON", "Démarrer la livraison"),
    "EN_LIVRAISON": ("LIVRE", "Confirmer la livraison"),
}


@role_required("logistique")
def missions(request):
    """Liste des missions (3 onglets : dispo, mes missions, terminées)."""
    me = request.session["user"]["nom"]
    all_missions = db.all_missions(request)
    tab = request.GET.get("onglet", "dispo")
    if tab == "mes":
        shown = [m for m in all_missions if m["livreur"] == me and m["statut"] != "LIVRE"]
    elif tab == "terminees":
        shown = [m for m in all_missions if m["livreur"] == me and m["statut"] == "LIVRE"]
    else:
        tab = "dispo"
        shown = [m for m in all_missions if m["livreur"] is None]
    return render(request, "core/logistique/missions.html", {"missions": shown, "tab": tab})


@role_required("logistique")
def mission_detail(request, pk):
    """Page de détail d'une mission avec bouton d'action."""
    mission = db.get_mission(request, pk)
    if mission is None:
        raise Http404("Mission introuvable")
    return render(request, "core/logistique/mission_detail.html", {
        "m": mission, "next_step": NEXT_STEP.get(mission["statut"]),
    })
