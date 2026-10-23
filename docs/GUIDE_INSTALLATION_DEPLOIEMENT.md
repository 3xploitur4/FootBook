# FootBook – Guide d'installation et de déploiement

Tâche Jira : SCRUM-62. Deux parties : lancer l'application sur son ordinateur (pour l'essayer), puis la mettre en ligne sur PythonAnywhere (gratuit, HTTPS fourni).

## 1. Essayer FootBook sur son ordinateur

Prérequis : Python 3.10 ou plus récent, Git.

```bash
git clone https://github.com/3xploitur4/FootBook.git
cd FootBook
git checkout claude/mvp-django        # tant que la branche n'est pas fusionnée dans main
cd Django
python -m venv venv
source venv/bin/activate              # Windows : venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py charger_demo
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000 dans le navigateur.

### Comptes de démonstration (mot de passe : `footbook2026`)

| Compte | Rôle | Ce qu'il permet de voir |
|---|---|---|
| `proprio1` | Propriétaire | 6 terrains ; une réservation aujourd'hui à 22:00 à valider (Terrain Maârif 5) |
| `proprio2` | Propriétaire | 6 terrains |
| `joueur1` | Joueur | 2 réservations à venir, une annonce publiée |
| `joueur2` | Joueur | 1 match joué, 1 réservation à venir |
| `joueur3` | Joueur | Participe à l'annonce de joueur1 |

`python manage.py charger_demo --reset` remet les données de démonstration à zéro.

### Essayer la validation d'un QR code en local

1. Se connecter en `joueur1`, ouvrir Mes réservations, puis le QR code de la réservation du jour, et copier le code texte.
2. Se déconnecter, se connecter en `proprio1`, ouvrir Valider un QR code et coller le code dans « Saisie manuelle ».

La caméra fonctionne sur `http://127.0.0.1` dans le navigateur de l'ordinateur. Sur un téléphone, il faut la version en ligne (HTTPS obligatoire).

### Lancer les tests

```bash
python manage.py test                 # 70 tests
```

## 2. Mise en ligne sur PythonAnywhere

1. **Compte** : créer un compte « Beginner » (gratuit) sur https://www.pythonanywhere.com. L'adresse du site sera `https://NOM.pythonanywhere.com` (NOM = votre nom d'utilisateur).
2. **Code** : onglet *Consoles* → *Bash*, puis :
   ```bash
   git clone https://github.com/3xploitur4/FootBook.git
   cd FootBook && git checkout claude/mvp-django
   mkvirtualenv --python=/usr/bin/python3.11 footbook
   pip install -r Django/requirements.txt
   ```
3. **Application web** : onglet *Web* → *Add a new web app* → *Manual configuration* → *Python 3.11*.
4. Dans l'onglet *Web*, renseigner :
   - *Source code* : `/home/NOM/FootBook/Django`
   - *Virtualenv* : `/home/NOM/.virtualenvs/footbook`
   - *Static files* : URL `/static/` → répertoire `/home/NOM/FootBook/Django/staticfiles`
   - *Force HTTPS* : activé (nécessaire pour la caméra du scan).
5. **Fichier WSGI** : cliquer sur le lien du fichier WSGI, tout remplacer par :
   ```python
   import os, sys
   chemin = "/home/NOM/FootBook/Django"
   if chemin not in sys.path:
       sys.path.insert(0, chemin)
   os.environ["DJANGO_SETTINGS_MODULE"] = "footbook.settings"
   os.environ["DJANGO_SECRET_KEY"] = "COLLER-ICI-UNE-LONGUE-CLE-ALEATOIRE"
   os.environ["DJANGO_DEBUG"] = "0"
   os.environ["DJANGO_ALLOWED_HOSTS"] = "NOM.pythonanywhere.com"
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
   Pour générer la clé, dans la console Bash : `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
6. **Base et fichiers statiques** : dans la console Bash (virtualenv actif) :
   ```bash
   cd ~/FootBook/Django
   export DJANGO_SECRET_KEY=temporaire DJANGO_DEBUG=0 DJANGO_ALLOWED_HOSTS=NOM.pythonanywhere.com
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py charger_demo
   python manage.py createsuperuser      # facultatif : accès à /admin/
   ```
7. **Recharger** : onglet *Web* → bouton *Reload*. Ouvrir `https://NOM.pythonanywhere.com`.

### Mettre à jour après une modification du code

```bash
cd ~/FootBook && git pull
workon footbook && cd Django
python manage.py migrate && python manage.py collectstatic --noinput
```
Puis *Reload* dans l'onglet *Web*.

### En cas de problème

| Symptôme | Cause probable | Solution |
|---|---|---|
| « Bad Request (400) » | `DJANGO_ALLOWED_HOSTS` ne contient pas l'adresse exacte | Corriger le fichier WSGI, *Reload* |
| Page sans mise en forme | Fichiers statiques non collectés ou mapping absent | `collectstatic`, vérifier *Static files* |
| « CSRF verification failed » | Adresse différente de `DJANGO_ALLOWED_HOSTS` | Même adresse dans le navigateur et dans le WSGI |
| La caméra ne s'ouvre pas | Site en HTTP ou permission refusée | *Force HTTPS*, autoriser la caméra ; la saisie manuelle reste possible |
| Erreur 500 | Voir l'*error log* dans l'onglet *Web* | — |

Le compte gratuit PythonAnywhere doit être prolongé tous les 3 mois (bouton dans l'onglet *Web*).
