from datetime import date

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from .models import Besoin, Categorie, DemandeAide, Don, Mission, Reservation, Utilisateur


class StatusActionTests(TestCase):
    def setUp(self):
        self.category = Categorie.objects.create(nom="Alimentation")
        self.donor = self.create_user("donateur", "donor@example.com")
        self.association = self.create_user("association", "association@example.com")
        self.beneficiary = self.create_user("beneficiaire", "beneficiary@example.com")
        self.logistician = self.create_user("logistique", "logistician@example.com")

    def create_user(self, role, email):
        return Utilisateur.objects.create(
            nom=email.split("@")[0],
            email=email,
            role=role,
            date_inscription=date.today(),
        )

    def post_action(self, user, kind, pk, code, next_url="/"):
        self.set_user_session(user)
        return self.client.post(
            reverse("change_status"),
            {"kind": kind, "pk": pk, "code": code, "next": next_url},
        )

    def set_user_session(self, user):
        session = self.client.session
        session["role"] = user.role
        session["user"] = {"nom": user.nom, "email": user.email}
        session.save()

    def create_donation(self, status="DISPONIBLE"):
        return Don.objects.create(
            ref=f"DON-{Don.objects.count() + 1}",
            titre="Colis alimentaire",
            categorie=self.category,
            description="Produits alimentaires",
            quantite=3,
            etat="Emballé",
            localisation="Tunis",
            statut=status,
            donateur=self.donor,
            date_publication=date.today(),
        )

    def test_association_can_accept_or_refuse_requests(self):
        accepted = self.create_request("EN_ATTENTE")
        refused = self.create_request("EN_ATTENTE")

        self.post_action(self.association, "request", accepted.pk, "VALIDE")
        self.post_action(self.association, "request", refused.pk, "REFUSE")

        accepted.refresh_from_db()
        refused.refresh_from_db()
        self.assertEqual(accepted.statut, "VALIDE")
        self.assertEqual(refused.statut, "REFUSE")

    def test_donation_form_creates_donation(self):
        self.set_user_session(self.donor)

        response = self.client.post(reverse("don_nouveau"), {
            "categorie": self.category.pk,
            "titre": "Vêtements chauds",
            "description": "Manteaux en bon état",
            "quantite": 4,
            "etat": "Bon",
            "localisation": "Tunis",
            "date_limite": "",
        })

        self.assertRedirects(response, reverse("mes_dons"))
        donation = Don.objects.get(titre="Vêtements chauds")
        self.assertEqual(donation.donateur, self.donor)
        self.assertEqual(donation.statut, "DISPONIBLE")

    def test_help_request_form_creates_pending_request(self):
        self.set_user_session(self.beneficiary)

        response = self.client.post(reverse("demande_nouvelle"), {
            "categorie": self.category.pk,
            "titre": "Aide alimentaire",
            "description": "Produits alimentaires de base",
            "quantite": 2,
            "motif": "Besoin familial",
            "priorite": "URGENTE",
            "localisation": "Tunis",
        })

        self.assertRedirects(response, reverse("mes_demandes"))
        help_request = DemandeAide.objects.get(titre="Aide alimentaire")
        self.assertEqual(help_request.beneficiaire, self.beneficiary)
        self.assertEqual(help_request.statut, "EN_ATTENTE")

    def test_need_form_creates_need(self):
        self.set_user_session(self.association)

        response = self.client.post(reverse("asso_besoin_nouveau"), {
            "categorie": self.category.pk,
            "description": "Couvertures",
            "quantite": 12,
            "priorite": "ELEVEE",
            "localisation": "Tunis",
        })

        self.assertRedirects(response, reverse("asso_besoins"))
        need = Besoin.objects.get(description="Couvertures")
        self.assertEqual(need.quantite, 12)

    def test_registration_button_creates_account_and_starts_session(self):
        response = self.client.post(reverse("register"), {
            "nom": "Nouvelle personne",
            "email": "new@example.com",
            "telephone": "12345678",
            "role": "beneficiaire",
            "mot_de_passe": "password123",
            "confirmation": "password123",
        })

        self.assertRedirects(response, reverse("dashboard"))
        user = Utilisateur.objects.get(email="new@example.com")
        self.assertEqual(self.client.session["user"]["email"], user.email)

    def test_login_button_starts_session(self):
        self.donor.password_hash = make_password("password123")
        self.donor.save(update_fields=["password_hash"])

        response = self.client.post(reverse("login"), {
            "email": self.donor.email,
            "mot_de_passe": "password123",
        })

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(self.client.session["user"]["email"], self.donor.email)

    def test_logout_link_clears_session(self):
        self.set_user_session(self.donor)

        response = self.client.get(reverse("logout"))

        self.assertRedirects(response, reverse("home"), target_status_code=302)
        self.assertNotIn("role", self.client.session)

    def test_donation_filter_returns_matching_results(self):
        self.create_donation()
        other = self.create_donation()
        other.titre = "Livres scolaires"
        other.save(update_fields=["titre"])
        self.set_user_session(self.association)

        response = self.client.get(reverse("dons_liste"), {"q": "Colis"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [donation["titre"] for donation in response.context["donations"]],
            ["Colis alimentaire"],
        )
    def test_beneficiary_can_confirm_receipt(self):
        help_request = self.create_request("EN_LIVRAISON")

        self.post_action(self.beneficiary, "request", help_request.pk, "RECU")

        help_request.refresh_from_db()
        self.assertEqual(help_request.statut, "RECU")

    def test_donor_can_accept_or_reject_reservation(self):
        accepted_donation = self.create_donation("RESERVE")
        refused_donation = self.create_donation("RESERVE")
        accepted = Reservation.objects.create(
            don=accepted_donation,
            association=self.association,
            quantite=accepted_donation.quantite,
        )
        refused = Reservation.objects.create(
            don=refused_donation,
            association=self.association,
            quantite=refused_donation.quantite,
        )

        self.post_action(self.donor, "reservation", accepted.pk, "CONFIRMEE")
        self.post_action(self.donor, "reservation", refused.pk, "REFUSEE")

        accepted.refresh_from_db()
        refused.refresh_from_db()
        refused_donation.refresh_from_db()
        self.assertEqual(accepted.statut, "CONFIRMEE")
        self.assertEqual(refused.statut, "REFUSEE")
        self.assertEqual(refused_donation.statut, "DISPONIBLE")

    def test_donation_status_actions_are_saved(self):
        donation = self.create_donation()

        self.post_action(self.association, "donation", donation.pk, "RESERVE")
        donation.refresh_from_db()
        self.assertEqual(donation.statut, "RESERVE")
        reservation = Reservation.objects.get(don=donation)

        self.post_action(self.donor, "reservation", reservation.pk, "CONFIRMEE")
        self.post_action(self.donor, "donation", donation.pk, "COLLECTE")
        self.post_action(self.association, "donation", donation.pk, "RECU")
        self.post_action(self.association, "donation", donation.pk, "DISTRIBUE")

        donation.refresh_from_db()
        self.assertEqual(donation.statut, "DISTRIBUE")

    def test_association_can_create_mission_after_donor_confirms(self):
        donation = self.create_donation("RESERVE")
        Reservation.objects.create(
            don=donation,
            association=self.association,
            quantite=donation.quantite,
            statut="CONFIRMEE",
        )

        self.post_action(self.association, "mission", donation.pk, "CREE")

        mission = Mission.objects.get(don=donation)
        self.assertEqual(mission.statut, "CREE")
        self.assertEqual(mission.point_livraison, self.association.ville or donation.localisation)

    def test_delivery_actions_update_mission_and_donation(self):
        donation = self.create_donation("RESERVE")
        mission = Mission.objects.create(
            don=donation,
            point_collecte="Tunis",
            point_livraison="Tunis",
            distance_km=5,
            type_livreur="Vélo",
            date_creation=date.today(),
        )

        self.post_action(self.logistician, "delivery", mission.pk, "ACCEPTE")
        self.post_action(self.logistician, "delivery", mission.pk, "EN_ROUTE")
        self.post_action(self.logistician, "delivery", mission.pk, "RECUPERE")
        donation.refresh_from_db()
        self.assertEqual(donation.statut, "COLLECTE")
        self.post_action(self.logistician, "delivery", mission.pk, "EN_LIVRAISON")
        self.post_action(self.logistician, "delivery", mission.pk, "LIVRE")

        mission.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(mission.statut, "LIVRE")
        self.assertEqual(donation.statut, "RECU")

    def create_request(self, status):
        return DemandeAide.objects.create(
            beneficiaire=self.beneficiary,
            categorie=self.category,
            titre="Besoin alimentaire",
            description="Demande de produits alimentaires",
            quantite=2,
            motif="Besoin urgent",
            priorite="MOYENNE",
            localisation="Tunis",
            statut=status,
            date_creation=date.today(),
        )

    def test_mot_de_passe_oublie_flux_complet(self):
        from django.core import signing
        # 1. Demande de réinitialisation
        response = self.client.post(reverse("mot_de_passe_oublie"), {
            "email": self.donor.email,
        })
        self.assertRedirects(response, reverse("login"))

        # 2. Utilisation du token généré
        token = signing.dumps({"email": self.donor.email}, salt="pwd-reset")
        response = self.client.post(reverse("reinitialiser_mot_de_passe", args=[token]), {
            "nouveau_mot_de_passe": "nouveauPass123",
            "confirmation": "nouveauPass123",
        })
        self.assertRedirects(response, reverse("login"))

        # 3. Vérification de la connexion avec le nouveau mot de passe
        response = self.client.post(reverse("login"), {
            "email": self.donor.email,
            "mot_de_passe": "nouveauPass123",
        })
        self.assertRedirects(response, reverse("dashboard"))
