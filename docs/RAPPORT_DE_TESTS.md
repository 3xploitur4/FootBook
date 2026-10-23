# FootBook – Rapport de tests et matrice de traçabilité

Tâches Jira : SCRUM-63 (tests d'intégration et de validation) et SCRUM-64 (matrice de traçabilité, rapport de tests).
Version testée : branche `claude/mvp-django`, Django 5.1.4, SQLite, le 23/10/2026.

## 1. Synthèse

| Niveau | Outil | Nombre | Résultat |
|---|---|---|---|
| Tests unitaires et d'intégration Django (TS1 à TS4) | `python manage.py test` (TestCase, client de test) | 70 | **70 réussis, 0 échec** |
| Test de bout en bout dans un navigateur | `scripts/parcours_e2e.py` (Playwright, Chromium, écran 1440×900) | 12 étapes | **12 réussies** |
| Scénarios de validation (SCRUM-60) | couverts par les deux niveaux ci-dessus | 28 | **27 réussis, 1 à confirmer à la main** (lecture du QR par l'appareil photo d'un téléphone) |

Aucune anomalie bloquante ouverte. Les anomalies trouvées et corrigées pendant les tests sont listées en section 5.

## 2. Comment rejouer les tests

```bash
cd Django
python manage.py test                       # 70 tests, environ 1 min 30
python manage.py charger_demo --reset       # jeu de démonstration
python manage.py runserver                  # dans un autre terminal
pip install playwright && playwright install chromium   # une seule fois
python scripts/parcours_e2e.py http://127.0.0.1:8000 ../docs/captures
```

Le parcours de bout en bout réserve le dernier créneau libre du jour. Lancé après 22:00, il réserve le lendemain, et l'étape E11 vérifie alors le refus « prévue le … » (cas V4) au lieu de la validation.

## 3. Tests unitaires par sprint

| Tâche | Fichier | Classes de test | Nb | Ce qui est vérifié |
|---|---|---|---|---|
| TS1 (SCRUM-52) | `comptes/tests.py` | InscriptionTests, ConnexionTests, AccesParRoleTests | 14 | Inscription valide (compte connecté, matchs_joues = 0, mot de passe `pbkdf2_sha256$`), email en double (R1), rôle hors liste (R2), mots de passe différents, prénom/nom obligatoires ; connexion réussie/échouée, retour à la page demandée, déconnexion en POST ; pour chaque page : visiteur → connexion, mauvais rôle → 403, bon rôle → 200 ; menu selon le rôle |
| TS1 (SCRUM-52) | `terrains/tests.py` | GestionTerrainsTests, RechercheTests | 18 | Propriétaire imposé (R6), prix ≤ 0 refusé (R4, formulaire et base), nom en double refusé pour le même propriétaire et accepté pour un autre (R5), modifier/supprimer le terrain d'un autre → 404 (A4), terrain réservé non supprimable, suppression en cascade (R7) ; filtres seuls et combinés, tri par prix, aucun résultat, prix min > max, valeur hors liste, une seule requête SQL pour la liste |
| TS2 (SCRUM-56) | `reservations/tests.py` | ReservationTests, QRCodeTests, ValidationTests (V1–V4) | 21 | Réservation valide (CONFIRMEE, code de 22 caractères), créneau pris refusé (EF-03), double réservation simultanée (IntegrityError), contrainte d'unicité en base, dates/heures hors plage, créneaux passés du jour absents, joueur imposé, propriétaire → 403 ; 500 codes tous différents ; QR d'un autre joueur → 404 (A3) ; validation réussie, code mal formé (V1), inconnu ou terrain d'un autre (V2, même message), déjà validée (V3), autre jour (V4), scan simultané |
| TS3 (SCRUM-58) | `reservations/tests.py`, `annonces/tests.py` | HistoriquesTests, ValidationTests, PublierTests, RejoindreTests | 14 | À venir / passées, réservations reçues limitées à ses terrains ; matchs_joues +1 pour l'auteur et les participants, pas de double comptage ; une annonce par réservation (B1), réservation d'un autre / passée / validée → 404 (B2), bornes 1 à 9/13/21 (B3) ; rejoindre décrémente et ferme à 0, annonce complète (B4), double participation (B5), auteur refusé, match passé masqué et refusé (B6), GET → 405 |
| TS4 (SCRUM-61) | `comptes/tests.py` | ProfilJoueurTests | 3 | Nom et matchs joués affichés, email absent ; profil d'un propriétaire ou inconnu → 404 ; visiteur → connexion, propriétaire → 403 |

Total : 70 tests. Couverture de code non mesurée (le paquet `coverage` n'a pas été utilisé).

## 4. Scénarios de validation (SCRUM-60) – résultats

Colonnes « Obtenu » et « Statut » du document SCRUM-60. « E » = étape du parcours navigateur ; les noms de tests sont ceux de la section 3.

| ID | Exigence | Scénario | Vérifié par | Obtenu | Statut |
|---|---|---|---|---|---|
| TV-01 | EF-01 | Inscription valide | E3, `test_inscription_valide_connecte_et_redirige_vers_espace` | Compte créé, connecté, tableau de bord | Réussi |
| TV-02 | EF-01 | Inscription avec un email existant | `test_email_deja_utilise_refuse` | « Un compte utilise déjà cette adresse email. », aucun compte | Réussi |
| TV-03 | EF-01 | Mauvais mot de passe | `test_connexion_echouee_message` | « Nom d'utilisateur ou mot de passe incorrect. » | Réussi |
| TV-04 | ENF-03 | Mots de passe hachés | `test_inscription_valide…` (préfixe `pbkdf2_sha256$`) | Haché | Réussi |
| TV-05 | ENF-03 | Visiteur sur /terrains/ | E2, `test_retour_a_la_page_demandee` | Connexion puis retour sur /terrains/ | Réussi |
| TV-06 | ENF-03 | Mauvais rôle | E5, `test_pages_joueur`, `test_pages_proprietaire` | 403 avec lien vers le tableau de bord | Réussi |
| TV-07 | EF-09 | Ajout d'un terrain | E4, E6, `test_ajout_valide_impose_le_proprietaire` | Visible dans Mes terrains et dans Terrains | Réussi |
| TV-08 | EF-09 | Prix 0 ; nom en double | E4, `test_prix_nul_ou_negatif_refuse`, `test_nom_en_double_refuse…` | Messages d'erreur, rien d'enregistré | Réussi |
| TV-09 | EF-09 | Modifier le terrain d'un autre | `test_modifier_ou_supprimer_le_terrain_d_un_autre_404` | 404 | Réussi |
| TV-10 | EF-02 | Liste sans filtre | `test_sans_filtre_tous_tries_par_prix` | Tous, par prix croissant, nombre affiché | Réussi |
| TV-11 | EF-02 | Trois filtres | E6, `test_filtres_combines` | Seuls les terrains correspondants | Réussi |
| TV-12 | EF-02 | Prix min > prix max | `test_prix_min_superieur_au_max` | Message d'erreur, liste complète | Réussi |
| TV-13 | EF-12 | Réserver un créneau | E7, `test_reservation_valide_redirige_vers_qr` | Confirmée, page du QR code | Réussi |
| TV-14 | EF-03 | Même créneau, deux joueurs | `test_double_reservation_simultanee`, `test_contrainte_unicite_en_base` | Une seule réservation ; « Ce créneau vient d'être réservé… » | Réussi |
| TV-15 | EF-12 | Créneaux passés ; J+15 | `test_creneaux_passes_du_jour_absents`, `test_date_et_heure_hors_plage_refusees` | Absents ; J+15 refusé | Réussi |
| TV-16 | EF-04 | QR code lisible | E7 (SVG affiché + code texte) | QR et code affichés | **À confirmer** : lecture par l'appareil photo d'un téléphone, sur la version déployée |
| TV-17 | EF-04 | QR d'un autre joueur | `test_qr_d_un_autre_joueur_404` | 404 | Réussi |
| TV-18 | EF-05 | Validation du jour | E11, `test_validation_reussie` | « Réservation validée », statut Validée | Réussi |
| TV-19 | ENF-04 | Second scan | E11, `test_v3_deja_validee`, `test_scan_simultane_un_seul_compte` | « Déjà validée le … », rien ne change | Réussi |
| TV-20 | EF-05 | Autre propriétaire ; « abc » | E11, `test_v2_terrain_d_un_autre_proprietaire_meme_message`, `test_v1_format_invalide` | Messages attendus | Réussi |
| TV-21 | EF-13 | Réservations reçues | E10, `test_reservations_recues_limitees_a_ses_terrains` | Seulement ses terrains, toutes les colonnes | Réussi |
| TV-22 | EF-10 | Mes réservations | `test_mes_reservations_separe_a_venir_et_passees` | À venir / passées, lien QR | Réussi |
| TV-23 | EF-06 | Publier une annonce | E8, `test_publication_valide` | Visible dans Annonces | Réussi |
| TV-24 | EF-06 | Seconde annonce | `test_b1_une_seule_annonce` | Refus (404) | Réussi |
| TV-25 | EF-07 | Rejoindre jusqu'à 0 | E9, `test_rejoindre_decremente_et_ferme_a_zero` | 2 → 1 → 0, annonce fermée | Réussi |
| TV-26 | EF-07 | Double participation ; auteur | `test_b5_pas_de_double_participation`, `test_auteur_ne_rejoint_pas_sa_propre_annonce` | Deux refus | Réussi |
| TV-27 | EF-08 | Matchs joués après validation | E12, `test_participants_comptes` | +1 pour l'auteur et chaque participant | Réussi |
| TV-28 | EF-11 | Profil d'un joueur | E12, `test_profil_affiche_nom_et_matchs_sans_email` | Nom, matchs, membre depuis ; pas d'email | Réussi |

## 5. Anomalies trouvées et corrigées

| # | Anomalie | Gravité | Correction |
|---|---|---|---|
| A1 | `select_for_update()` prévu dans la conception ne verrouille rien sous SQLite : deux scans simultanés pouvaient valider deux fois | Haute | Mise à jour conditionnelle `filter(statut=CONFIRMEE).update(...)` ; test `test_scan_simultane_un_seul_compte` |
| A2 | Même risque pour la dernière place d'une annonce | Haute | Décrément conditionnel dans une transaction ; tests B4/B5 |
| A3 | En production derrière le proxy HTTPS de l'hébergeur, `SECURE_SSL_REDIRECT` provoquait une boucle de redirection et les POST échouaient au contrôle CSRF | Haute | `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS` calculé depuis `DJANGO_ALLOWED_HOSTS` ; redirection HTTPS laissée à l'hébergeur |
| A4 | Bootstrap et le lecteur QR chargés depuis des CDN : application inutilisable sans accès à ces domaines | Moyenne | Bibliothèques copiées dans `static/vendor/` (Bootstrap 5.3.3, Bootstrap Icons 1.11.3, html5-qrcode 2.3.8) |
| A5 | Interface pensée pour mobile (colonne de 560 px) | Moyenne | Refonte en application web : barre latérale, tableau de bord, tableaux, mises en page sur plusieurs colonnes ; reste utilisable sur tablette et téléphone |

## 6. Matrice de traçabilité

| Exigence | User story | Tâches de code | Tests unitaires | Scénarios | Statut |
|---|---|---|---|---|---|
| EF-01 Comptes et rôles | US-01 (SCRUM-12) | SCRUM-24, 25, 26 | InscriptionTests, ConnexionTests, AccesParRoleTests | TV-01, 02, 03 | Couvert |
| EF-02 Recherche filtrée | US-03 (SCRUM-14) | SCRUM-30, 31 | RechercheTests | TV-10, 11, 12 | Couvert |
| EF-03 Pas de double réservation | US-04 (SCRUM-15) | SCRUM-32, 33 | `test_creneau_deja_pris_refuse`, `test_double_reservation_simultanee`, `test_contrainte_unicite_en_base` | TV-14 | Couvert |
| EF-04 QR code par réservation | US-05 (SCRUM-16) | SCRUM-34, 35 | QRCodeTests, `test_codes_uniques_et_imprevisibles` | TV-16, 17 | Couvert (TV-16 à confirmer sur téléphone) |
| EF-05 Validation du QR | US-06 (SCRUM-17) | SCRUM-36, 37 | ValidationTests | TV-18, 20 | Couvert |
| EF-06 Publier une annonce | US-10 (SCRUM-21) | SCRUM-42, 43 | PublierTests | TV-23, 24 | Couvert |
| EF-07 Rejoindre une annonce | US-11 (SCRUM-22) | SCRUM-44, 45 | RejoindreTests | TV-25, 26 | Couvert |
| EF-08 Matchs joués | US-09 (SCRUM-20) | SCRUM-40, 41 | `test_validation_reussie`, `test_v3_deja_validee`, `test_participants_comptes` | TV-27 | Couvert |
| EF-09 Gestion des terrains | US-02 (SCRUM-13) | SCRUM-27, 28, 29 | GestionTerrainsTests | TV-07, 08, 09 | Couvert |
| EF-10 Historique du joueur | US-08 (SCRUM-19) | SCRUM-39 | `test_mes_reservations_separe_a_venir_et_passees` | TV-22 | Couvert |
| EF-11 Profil d'un joueur | US-12 (SCRUM-23) | SCRUM-46 | ProfilJoueurTests | TV-28 | Couvert |
| EF-12 Réserver un créneau | US-04 (SCRUM-15) | SCRUM-32, 33 | ReservationTests | TV-13, 15 | Couvert (libellé exact à vérifier dans le cahier des charges) |
| EF-13 Réservations reçues | US-07 (SCRUM-18) | SCRUM-38 | `test_reservations_recues_limitees_a_ses_terrains` | TV-21 | Couvert |
| ENF-03 Sécurité (hachage, accès par rôle) | US-01 | SCRUM-26 | `test_inscription_valide…`, AccesParRoleTests | TV-04, 05, 06 | Couvert |
| ENF-04 QR à usage unique | US-06 | SCRUM-37 | `test_v3_deja_validee`, `test_scan_simultane_un_seul_compte` | TV-19 | Couvert |

Toutes les exigences ont au moins une user story, une tâche de code, un test automatisé et un scénario de validation.

## 7. Captures du parcours

Les 18 captures d'écran produites par le parcours de bout en bout sont dans `docs/captures/` (01_accueil.png à 18_profil.png).
