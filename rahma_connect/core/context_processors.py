from . import data as db

MENUS = {
    "donateur": [
        ("Tableau de bord", "dashboard"),
        ("Mes dons", "mes_dons"),
        ("Publier un don", "don_nouveau"),
        ("Réservations", "reservations"),
        ("Mon profil", "profil"),
    ],
    "beneficiaire": [
        ("Tableau de bord", "dashboard"),
        ("Nouvelle demande", "demande_nouvelle"),
        ("Mes demandes", "mes_demandes"),
        ("Mon profil", "profil"),
    ],
    "association": [
        ("Tableau de bord", "dashboard"),
        ("Demandes à valider", "asso_demandes"),
        ("Besoins", "asso_besoins"),
        ("Dons disponibles", "dons_liste"),
        ("Stock", "asso_stock"),
        ("Collecte et distribution", "asso_distribution"),
        ("Mon profil", "profil"),
    ],
    "logistique": [
        ("Tableau de bord", "dashboard"),
        ("Missions", "missions"),
        ("Mon profil", "profil"),
    ],
    "admin": [
        ("Tableau de bord", "dashboard"),
        ("Utilisateurs", "admin_utilisateurs"),
        ("Associations", "admin_associations"),
        ("Catégories", "admin_categories"),
        ("Mon profil", "profil"),
    ],
}

ADMIN_EXTRA = [
    ("Demandes à valider", "asso_demandes"),
    ("Dons disponibles", "dons_liste"),
    ("Missions", "missions"),
]


def rahma(request):
    role = request.session.get("role")

    ctx = {
        "role": role,
    }

    if role:
        current_url_name = request.resolver_match.url_name if request.resolver_match else ""

        def build_menu(items):
            return [
                {
                    "label": label,
                    "url": name,
                    "active": name == current_url_name,
                }
                for label, name in items
            ]

        ctx["current_user"] = request.session["user"]
        ctx["role_label"] = db.ROLES[role]
        ctx["menu"] = build_menu(MENUS[role])
        ctx["menu_extra"] = build_menu(ADMIN_EXTRA) if role == "admin" else []

    return ctx
