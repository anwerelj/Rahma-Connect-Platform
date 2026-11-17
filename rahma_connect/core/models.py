from django.db import models


class Categorie(models.Model):
    nom = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.nom


class Utilisateur(models.Model):
    ROLES = [
        ("donateur",     "Donateur"),
        ("association",  "Association"),
        ("beneficiaire", "Bénéficiaire"),
        ("logistique",   "Partenaire logistique"),
        ("admin",        "Administrateur"),
    ]
    nom       = models.CharField(max_length=100)
    email     = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    ville     = models.CharField(max_length=80, blank=True)
    role      = models.CharField(max_length=20, choices=ROLES)
    password_hash = models.CharField(max_length=128, blank=True)
    actif     = models.BooleanField(default=True)
    date_inscription = models.DateField()

    def __str__(self):
        return f"{self.nom} ({self.get_role_display()})"


class Don(models.Model):
    ETATS = [
        ("Neuf",    "Neuf"),
        ("Très bon","Très bon état"),
        ("Bon",     "Bon état"),
        ("Usagé",   "Usagé"),
        ("Frais",   "Frais (alimentaire)"),
        ("Emballé", "Emballé (alimentaire)"),
    ]
    STATUTS = [
        ("DISPONIBLE", "Disponible"),
        ("RESERVE",    "Réservé"),
        ("COLLECTE",   "Collecté"),
        ("RECU",       "Reçu"),
        ("DISTRIBUE",  "Distribué"),
        ("ANNULE",     "Annulé"),
    ]

    ref              = models.CharField(max_length=30, unique=True)
    titre            = models.CharField(max_length=80)
    categorie        = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    description      = models.TextField()
    quantite         = models.PositiveIntegerField()
    etat             = models.CharField(max_length=20, choices=ETATS)
    localisation     = models.CharField(max_length=80)
    distance_km      = models.PositiveIntegerField(default=0)
    statut           = models.CharField(max_length=20, choices=STATUTS, default="DISPONIBLE")
    donateur         = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="dons")
    date_publication = models.DateField()
    date_limite      = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.ref} — {self.titre}"


class Reservation(models.Model):
    STATUTS = [
        ("EN_ATTENTE", "En attente"),
        ("CONFIRMEE", "Confirmée"),
        ("REFUSEE", "Refusée"),
    ]

    don = models.ForeignKey(Don, on_delete=models.CASCADE, related_name="reservations")
    association = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="reservations")
    quantite = models.PositiveIntegerField()
    statut = models.CharField(max_length=20, choices=STATUTS, default="EN_ATTENTE")
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Réservation du don #{self.don_id} — {self.get_statut_display()}"


class DemandeAide(models.Model):
    PRIORITES = [
        ("FAIBLE",  "Faible"),
        ("MOYENNE", "Moyenne"),
        ("ELEVEE",  "Élevée"),
        ("URGENTE", "Urgente"),
    ]
    STATUTS = [
        ("CREE",         "Créée"),
        ("EN_ATTENTE",   "En attente de validation"),
        ("VALIDE",       "Validée"),
        ("REFUSE",       "Refusée"),
        ("DON_TROUVE",   "Don trouvé"),
        ("EN_LIVRAISON", "Livraison en cours"),
        ("RECU",         "Reçue"),
    ]

    beneficiaire  = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="demandes")
    categorie     = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    titre         = models.CharField(max_length=80)
    description   = models.TextField()
    quantite      = models.PositiveIntegerField()
    motif         = models.CharField(max_length=200)
    priorite      = models.CharField(max_length=10, choices=PRIORITES, default="MOYENNE")
    localisation  = models.CharField(max_length=80)
    statut        = models.CharField(max_length=20, choices=STATUTS, default="CREE")
    date_creation = models.DateField()

    def __str__(self):
        return f"Demande #{self.pk} — {self.titre}"


class Besoin(models.Model):
    categorie    = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    description  = models.CharField(max_length=200)
    quantite     = models.PositiveIntegerField()
    priorite     = models.CharField(max_length=10)
    localisation = models.CharField(max_length=80)
    statut       = models.CharField(max_length=20, default="Actif")

    def __str__(self):
        return f"Besoin #{self.pk} — {self.description[:40]}"


class Stock(models.Model):
    nom               = models.CharField(max_length=80)
    categorie         = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    quantite_actuelle = models.PositiveIntegerField()
    stock_min         = models.PositiveIntegerField()
    stock_max         = models.PositiveIntegerField()

    def __str__(self):
        return self.nom

    def est_faible(self):
        return self.quantite_actuelle < self.stock_min


class Mission(models.Model):
    STATUTS = [
        ("CREE",         "Créée"),
        ("ACCEPTE",      "Acceptée"),
        ("EN_ROUTE",     "En route"),
        ("RECUPERE",     "Don récupéré"),
        ("EN_LIVRAISON", "En livraison"),
        ("LIVRE",        "Livré"),
    ]

    don              = models.ForeignKey(Don, on_delete=models.CASCADE)
    point_collecte   = models.CharField(max_length=150)
    point_livraison  = models.CharField(max_length=150)
    distance_km      = models.PositiveIntegerField()
    type_livreur     = models.CharField(max_length=50)
    statut           = models.CharField(max_length=20, choices=STATUTS, default="CREE")
    livreur          = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name="missions")
    date_creation    = models.DateField()

    def __str__(self):
        return f"Mission #{self.pk} — {self.don.titre}"
