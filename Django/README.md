# FootBook – application Django

## Installation

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py charger_demo          # --reset pour recréer les données
python manage.py runserver
```

Comptes de démonstration (mot de passe `footbook2026`) :

| Compte | Rôle |
|---|---|
| proprio1, proprio2 | Propriétaire |
| joueur1, joueur2, joueur3 | Joueur |

`joueur1` a une réservation aujourd'hui à 22:00 sur « Terrain Maârif 5 » (proprio1) : elle sert à tester la validation par QR code.

## Structure

| Application | Rôle | User stories |
|---|---|---|
| `comptes` | Utilisateur (rôle, matchs joués), inscription, connexion, espace, profil | US-01, US-12 |
| `terrains` | CRUD des terrains du propriétaire, recherche filtrée | US-02, US-03 |
| `reservations` | Créneaux, réservation, QR code, validation, historiques | US-04 à US-09 |
| `annonces` | Publier et rejoindre une annonce | US-10, US-11 |

Règles importantes :
- Accès : visiteur → page de connexion, mauvais rôle → 403 (`comptes/permissions.py`).
- Double réservation : contrainte d'unicité (terrain, date, heure) en base.
- Validation du QR et « rejoindre » : mises à jour conditionnelles (SQLite ignore `select_for_update`).

## Tests

```bash
python manage.py test        # 69 tests
```

TS1 (SCRUM-52) `comptes/tests.py`, `terrains/tests.py` · TS2/TS3 (SCRUM-56, 58) `reservations/tests.py` · TS4 (SCRUM-61) `annonces/tests.py`, `comptes/tests.py`.

## Production

Variables d'environnement : `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS=moncompte.pythonanywhere.com`, puis `python manage.py collectstatic`.
