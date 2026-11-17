"""
data.py — Couche d'accès aux données

Ce fichier fournit une interface simple pour accéder aux données
de la base via l'ORM Django. Il convertit les objets Django en dictionnaires
pour garder la compatibilité avec les templates existants.
"""

from .models import Categorie, Don, DemandeAide, Besoin, Stock, Mission


ROLES = {
    "donateur": "Donateur",
    "association": "Association",
    "beneficiaire": "Bénéficiaire",
    "logistique": "Partenaire logistique",
    "admin": "Administrateur",
}

# Proxy pour accéder aux catégories comme une liste
class _CategoriesProxy:
    """Permet d'accéder aux catégories de la DB comme une liste"""
    _cache = None
    
    def _get_all(self):
        if self._cache is None:
            self._cache = [
                {"id": c.id, "nom": c.nom, "description": c.description}
                for c in Categorie.objects.all()
            ]
        return self._cache
    
    def __iter__(self):
        return iter(self._get_all())
    
    def __getitem__(self, key):
        return self._get_all()[key]
    
    def __len__(self):
        return len(self._get_all())


CATEGORIES = _CategoriesProxy()


# Statuts et leurs affichages (label, couleur)
DONATION_STATUS = {
    "DISPONIBLE": ("Disponible", "green"),
    "RESERVE": ("Réservé", "amber"),
    "COLLECTE": ("Collecté", "blue"),
    "RECU": ("Reçu", "blue"),
    "DISTRIBUE": ("Distribué", "purple"),
    "ANNULE": ("Annulé", "red"),
}

REQUEST_STATUS = {
    "CREE": ("Créée", "gray"),
    "EN_ATTENTE": ("En attente de validation", "amber"),
    "VALIDE": ("Validée par l'association", "green"),
    "REFUSE": ("Refusée", "red"),
    "DON_TROUVE": ("Don trouvé", "blue"),
    "EN_LIVRAISON": ("Livraison en cours", "blue"),
    "RECU": ("Reçue", "purple"),
}

DELIVERY_STATUS = {
    "CREE": ("Créée", "gray"),
    "ACCEPTE": ("Acceptée", "amber"),
    "EN_ROUTE": ("En route", "blue"),
    "RECUPERE": ("Don récupéré", "blue"),
    "EN_LIVRAISON": ("En livraison", "blue"),
    "LIVRE": ("Livré", "purple"),
}

PRIORITY = {
    "FAIBLE": ("Faible", "gray"),
    "MOYENNE": ("Moyenne", "blue"),
    "ELEVEE": ("Élevée", "amber"),
    "URGENTE": ("Urgente", "red"),
}

# Table de correspondance pour les badges dans les templates
STATUS_TABLES = {
    "donation": DONATION_STATUS,
    "request": REQUEST_STATUS,
    "delivery": DELIVERY_STATUS,
    "priority": PRIORITY,
}

# Étapes de progression pour chaque type
STEPS = {
    "donation": ["DISPONIBLE", "RESERVE", "COLLECTE", "RECU", "DISTRIBUE"],
    "request": ["CREE", "EN_ATTENTE", "VALIDE", "DON_TROUVE", "EN_LIVRAISON", "RECU"],
    "delivery": ["CREE", "ACCEPTE", "EN_ROUTE", "RECUPERE", "EN_LIVRAISON", "LIVRE"],
}


def get_category(cat_id):
    """Récupère une catégorie par son ID"""
    try:
        c = Categorie.objects.get(id=cat_id)
        return {"id": c.id, "nom": c.nom, "description": c.description}
    except Categorie.DoesNotExist:
        return {"id": 0, "nom": "Autre", "description": ""}


def _with_cat(item):
    """Enrichit un dictionnaire avec les infos de sa catégorie"""
    item = dict(item)
    c = get_category(item["categorie"])
    item["cat_nom"] = c["nom"]
    return item


def _don_to_dict(don):
    """Convertit un objet Don en dictionnaire pour les templates"""
    return {
        "id": don.id,
        "ref": don.ref,
        "titre": don.titre,
        "categorie": don.categorie.id,
        "description": don.description,
        "quantite": don.quantite,
        "etat": don.etat,
        "localisation": don.localisation,
        "distance_km": don.distance_km,
        "statut": don.statut,
        "donateur": don.donateur.nom,
        "date_limite": don.date_limite,
        "date_publication": don.date_publication,
    }


def _request_to_dict(req):
    """Convertit une DemandeAide en dictionnaire"""
    return {
        "id": req.id,
        "beneficiaire": req.beneficiaire.nom,
        "categorie": req.categorie.id,
        "titre": req.titre,
        "description": req.description,
        "quantite": req.quantite,
        "motif": req.motif,
        "priorite": req.priorite,
        "localisation": req.localisation,
        "statut": req.statut,
        "date_creation": req.date_creation,
    }


def _need_to_dict(need):
    """Convertit un Besoin en dictionnaire"""
    return {
        "id": need.id,
        "categorie": need.categorie.id,
        "description": need.description,
        "quantite": need.quantite,
        "priorite": need.priorite,
        "localisation": need.localisation,
        "statut": need.statut,
    }


def _mission_to_dict(mission):
    """Convertit une Mission en dictionnaire"""
    return {
        "id": mission.id,
        "don": {
            "id": mission.don.id,
            "titre": mission.don.titre,
            "ref": mission.don.ref,
        },
        "point_collecte": mission.point_collecte,
        "point_livraison": mission.point_livraison,
        "distance_km": mission.distance_km,
        "type_livreur": mission.type_livreur,
        "statut": mission.statut,
        "livreur": mission.livreur.nom if mission.livreur else None,
        "date_creation": mission.date_creation,
    }


# ---------------------------------------------------------------------------
# Accès aux données (via l'ORM Django)
# ---------------------------------------------------------------------------

def all_donations(request):
    """Récupère tous les dons de la base de données"""
    dons = Don.objects.select_related('categorie', 'donateur').all()
    return [_with_cat(_don_to_dict(d)) for d in dons]


def get_donation(request, pk):
    """Récupère un don par son ID"""
    try:
        don = Don.objects.select_related('categorie', 'donateur').get(id=pk)
        return _with_cat(_don_to_dict(don))
    except Don.DoesNotExist:
        return None


def all_requests(request):
    """Récupère toutes les demandes d'aide"""
    reqs = DemandeAide.objects.select_related('categorie', 'beneficiaire').all()
    return [_with_cat(_request_to_dict(r)) for r in reqs]


def get_request(request, pk):
    """Récupère une demande par son ID"""
    try:
        req = DemandeAide.objects.select_related('categorie', 'beneficiaire').get(id=pk)
        return _with_cat(_request_to_dict(req))
    except DemandeAide.DoesNotExist:
        return None


def all_needs(request):
    """Récupère tous les besoins de l'association"""
    needs = Besoin.objects.select_related('categorie').all()
    return [_with_cat(_need_to_dict(n)) for n in needs]


def get_stock_items():
    """Récupère tous les articles en stock avec leurs niveaux"""
    items = []
    for s in Stock.objects.select_related('categorie').all():
        item = {
            "id": s.id,
            "nom": s.nom,
            "categorie": s.categorie.id,
            "quantite_actuelle": s.quantite_actuelle,
            "stock_min": s.stock_min,
            "stock_max": s.stock_max,
            "faible": s.quantite_actuelle < s.stock_min,
            "pourcent": min(100, round(100 * s.quantite_actuelle / s.stock_max)) if s.stock_max > 0 else 0,
        }
        items.append(_with_cat(item))
    return items


def all_missions(request):
    """Récupère toutes les missions de livraison"""
    missions = Mission.objects.select_related('don', 'livreur').all()
    return [_mission_to_dict(m) for m in missions]


def get_mission(request, pk):
    """Récupère une mission par son ID"""
    try:
        mission = Mission.objects.select_related('don', 'livreur').get(id=pk)
        return _mission_to_dict(mission)
    except Mission.DoesNotExist:
        return None
