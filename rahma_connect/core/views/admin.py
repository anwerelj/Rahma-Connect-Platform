"""
Vues pour le rôle ADMINISTRATEUR.
Gestion des utilisateurs, associations et catégories.
"""

from django.shortcuts import render

from .. import data as db
from ..decorators import role_required
from ..models import Utilisateur


@role_required("admin")
def admin_utilisateurs(request):
    """Liste de tous les utilisateurs."""
    users = Utilisateur.objects.order_by("nom")
    return render(request, "core/admin/utilisateurs.html", {"users": users})


@role_required("admin")
def admin_associations(request):
    """Liste de toutes les associations."""
    associations = Utilisateur.objects.filter(role="association").order_by("nom")
    return render(request, "core/admin/associations.html", {"items": associations})


@role_required("admin")
def admin_categories(request):
    """Liste de toutes les catégories de dons."""
    return render(request, "core/admin/categories.html", {"categories": db.CATEGORIES})
