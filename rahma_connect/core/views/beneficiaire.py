"""
Vues pour le rôle BÉNÉFICIAIRE.
Gestion des demandes d'aide.
"""

from datetime import date
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

from .. import data as db
from ..decorators import role_required
from ..forms import HelpRequestForm
from ..models import Categorie, DemandeAide, Utilisateur


@role_required("beneficiaire")
def mes_demandes(request):
    """Liste des demandes d'aide du bénéficiaire."""
    me = request.session["user"]["nom"]
    mine = [r for r in db.all_requests(request) if r["beneficiaire"] == me]
    return render(request, "core/beneficiaire/mes_demandes.html", {"requests": mine[::-1]})


@role_required("beneficiaire")
def demande_nouvelle(request):
    """Formulaire pour soumettre une nouvelle demande d'aide."""
    form = HelpRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        actor = Utilisateur.objects.filter(email=request.session["user"]["email"]).first()
        if actor is None:
            messages.error(request, "Votre session ne correspond plus à un utilisateur actif.")
        else:
            data = form.cleaned_data
            DemandeAide.objects.create(
                beneficiaire=actor,
                categorie=Categorie.objects.get(pk=data["categorie"]),
                titre=data["titre"],
                description=data["description"],
                quantite=data["quantite"],
                motif=data["motif"],
                priorite=data["priorite"],
                localisation=data["localisation"],
                statut="EN_ATTENTE",
                date_creation=date.today(),
            )
            messages.success(request, "Votre demande a été envoyée. Une association va l'examiner.")
            return redirect("mes_demandes")
    return render(request, "core/beneficiaire/demande_form.html", {"form": form})


@role_required("beneficiaire", "association")
def demande_detail(request, pk):
    """Page de détail d'une demande d'aide."""
    req = db.get_request(request, pk)
    if req is None:
        raise Http404("Demande introuvable")
    return render(request, "core/beneficiaire/demande_detail.html", {"req": req})
