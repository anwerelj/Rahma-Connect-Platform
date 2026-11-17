from getpass import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from core.models import Utilisateur


class Command(BaseCommand):
    help = "Définit le mot de passe d'un compte administrateur existant."

    def add_arguments(self, parser):
        parser.add_argument("email", nargs="?", default="admin@rahma.tn")

    def handle(self, *args, **options):
        email = options["email"].strip()
        try:
            admin = Utilisateur.objects.get(email__iexact=email, role="admin")
        except Utilisateur.DoesNotExist:
            raise CommandError(f"Aucun compte administrateur trouvé pour {email}.")
        except Utilisateur.MultipleObjectsReturned:
            raise CommandError(f"Plusieurs comptes administrateur correspondent à {email}.")

        password = getpass("Nouveau mot de passe (8 caractères minimum) : ")
        confirmation = getpass("Confirmer le mot de passe : ")
        if len(password) < 8:
            raise CommandError("Le mot de passe doit contenir au moins 8 caractères.")
        if password != confirmation:
            raise CommandError("Les deux mots de passe ne correspondent pas.")

        admin.password_hash = make_password(password)
        admin.save(update_fields=["password_hash"])
        self.stdout.write(self.style.SUCCESS(f"Mot de passe défini pour {admin.email}."))
