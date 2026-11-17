"""
Point d'entrée des URLs du projet.

Django lit ce fichier en premier. On délègue tout à core/urls.py
parce qu'on n'a qu'une seule app pour l'instant.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
]
