"""
Vue organisées par rôle.
Chaque acteur a son propre fichier.
"""

from .common import (
    home, login_view, register_view, logout_view, dashboard, profil, change_status,
    mot_de_passe_oublie, reinitialiser_mot_de_passe,
)
from .donateur import mes_dons, don_nouveau, reservations, donation_detail
from .beneficiaire import mes_demandes, demande_nouvelle, demande_detail
from .association import (
    donations_list, asso_demandes, asso_besoins, asso_besoin_nouveau,
    asso_stock, asso_distribution
)
from .logistique import missions, mission_detail
from .admin import admin_utilisateurs, admin_associations, admin_categories

__all__ = [
    # common
    'home', 'login_view', 'register_view', 'logout_view', 'dashboard', 'profil', 'change_status',
    'mot_de_passe_oublie', 'reinitialiser_mot_de_passe',
    # donateur
    'mes_dons', 'don_nouveau', 'reservations', 'donation_detail',
    # beneficiaire
    'mes_demandes', 'demande_nouvelle', 'demande_detail',
    # association
    'donations_list', 'asso_demandes', 'asso_besoins', 'asso_besoin_nouveau',
    'asso_stock', 'asso_distribution',
    # logistique
    'missions', 'mission_detail',
    # admin
    'admin_utilisateurs', 'admin_associations', 'admin_categories',
]
