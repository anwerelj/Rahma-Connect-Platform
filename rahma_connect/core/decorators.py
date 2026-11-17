from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapper(request, *args, **kwargs):
            role = request.session.get("role")

            if not role:
                messages.info(request, "Connectez-vous pour accéder à cette page.")
                return redirect("login")

            if role != "admin" and role not in roles:
                messages.error(request, "Votre rôle n'a pas accès à cette page.")
                return redirect("dashboard")

            return view_function(request, *args, **kwargs)
        return wrapper
    return decorator


# Raccourci pour les pages qui nécessitent juste d'être connecté,
# peu importe le rôle.
ALL_ROLES = ("donateur", "association", "beneficiaire", "logistique", "admin")
login_required = role_required(*ALL_ROLES)
