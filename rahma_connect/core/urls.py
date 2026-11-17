
from django.urls import path
from .views import (
    # Pages communes
    home, login_view, register_view, logout_view, dashboard, profil, change_status,
    mot_de_passe_oublie, reinitialiser_mot_de_passe,
    # Donateur
    mes_dons, don_nouveau, reservations, donation_detail,
    # Bénéficiaire
    mes_demandes, demande_nouvelle, demande_detail,
    # Association
    donations_list, asso_demandes, asso_besoins, asso_besoin_nouveau,
    asso_stock, asso_distribution,
    # Logistique
    missions, mission_detail,
    # Admin
    admin_utilisateurs, admin_associations, admin_categories,
)

urlpatterns = [

    # pages publiques, pas besoin d'être connecté
    path("", home, name="home"),
    path("connexion/", login_view, name="login"),
    path("inscription/", register_view, name="register"),
    path("deconnexion/", logout_view, name="logout"),
    path("mot-de-passe-oublie/", mot_de_passe_oublie, name="mot_de_passe_oublie"),
    path("reinitialisation-mot-de-passe/<str:token>/", reinitialiser_mot_de_passe, name="reinitialiser_mot_de_passe"),

    # pages communes à tous les rôles connectés
    path("tableau-de-bord/", dashboard, name="dashboard"),
    path("profil/", profil, name="profil"),
    path("action/", change_status, name="change_status"),

    # dons (partagés entre plusieurs rôles)
    path("dons/", donations_list, name="dons_liste"),
    path("dons/nouveau/", don_nouveau, name="don_nouveau"),
    path("dons/<int:pk>/", donation_detail, name="don_detail"),

    # pages du donateur
    path("mes-dons/", mes_dons, name="mes_dons"),
    path("reservations/", reservations, name="reservations"),

    # pages du bénéficiaire
    path("mes-demandes/", mes_demandes, name="mes_demandes"),
    path("demandes/nouvelle/", demande_nouvelle, name="demande_nouvelle"),
    path("demandes/<int:pk>/", demande_detail, name="demande_detail"),

    # pages de l'association
    path("association/demandes/", asso_demandes, name="asso_demandes"),
    path("association/besoins/", asso_besoins, name="asso_besoins"),
    path("association/besoins/nouveau/", asso_besoin_nouveau, name="asso_besoin_nouveau"),
    path("association/stock/", asso_stock, name="asso_stock"),
    path("association/distribution/", asso_distribution, name="asso_distribution"),

    # pages du partenaire logistique
    path("livraisons/", missions, name="missions"),
    path("livraisons/<int:pk>/", mission_detail, name="mission_detail"),

    # pages de l'administrateur
    path("gestion/utilisateurs/", admin_utilisateurs, name="admin_utilisateurs"),
    path("gestion/associations/", admin_associations, name="admin_associations"),
    path("gestion/categories/", admin_categories, name="admin_categories"),
]
