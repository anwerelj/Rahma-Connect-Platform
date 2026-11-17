
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Chargement du fichier .env local
env_file = BASE_DIR / ".env"
if env_file.is_file():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# Clé secrète pour le chiffrement (à changer en production)
SECRET_KEY = "dev-only-change-me-rahma-connect"

# Mode développement (à désactiver en production)
DEBUG = True

# Domaines autorisés (à restreindre en production)
ALLOWED_HOSTS = ["*"]


# Les apps Django qu'on utilise dans ce projet.
# "core" c'est notre application principale qu'on a créée.
INSTALLED_APPS = [
    "django.contrib.staticfiles",  # sert les fichiers CSS/JS
    "django.contrib.messages",     # les messages flash (succès, erreur...)
    "core",
]


# Le middleware, c'est une suite de fonctions qui s'exécutent
# à chaque requête HTTP avant d'arriver à la vue.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# Django lit ce fichier en premier pour trouver les URLs du projet.
ROOT_URLCONF = "config.urls"


# Configuration des templates HTML.
# APP_DIRS=True : Django cherche automatiquement les templates
# dans le dossier "templates/" de chaque app installée.
# Les context_processors injectent des variables dans tous les templates.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                # Ajoute le rôle et le menu à chaque page.
                "core.context_processors.rahma",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# SQLite : la base de données la plus simple, Django l'utilise par défaut.
# Le fichier db.sqlite3 sera créé automatiquement la première fois
# qu'on lance "python manage.py migrate".
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Les sessions sont stockées dans des fichiers au lieu d'une base de données.
# Chaque utilisateur a son propre fichier dans le dossier .sessions/.
(BASE_DIR / ".sessions").mkdir(exist_ok=True)
SESSION_ENGINE = "django.contrib.sessions.backends.file"
SESSION_FILE_PATH = str(BASE_DIR / ".sessions")


# Paramètres régionaux du projet.
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Tunis"
USE_I18N = False
USE_TZ = True


# Mailtrap Email Sandbox (SMTP)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "sandbox.smtp.mailtrap.io"
EMAIL_PORT = 2525
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "a0f48e7375567a")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Rahma Connect <noreply@rahma-connect.tn>")


STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
