# Network Monitor

Outil de supervision réseau en Python : il teste en continu la disponibilité de plusieurs machines, enregistre l'historique dans une base SQLite et l'affiche sur un tableau de bord web.

![Tableau de bord](dasboard.png)

## Fonctionnement

monitor.py (ping) -> monitor.db (SQLite) -> export.py (calculs) -> data.js -> index.html (affichage)

- `monitor.py` envoie un ping toutes les 30 secondes à chaque machine de la liste, mesure la latence et enregistre le résultat (machine, heure, état UP/DOWN, latence).
- `export.py` lit la base, calcule la disponibilité (%) et la latence moyenne de chaque machine, puis écrit `data.js`.
- `index.html` affiche l'état de chaque machine, une courbe de latence et les derniers pings. La page se rafraîchit toute seule.

## Technologies

Python 3 (modules standard : sqlite3, subprocess, json), SQLite, HTML, CSS, JavaScript.

## Utilisation

1. Lancer la collecte : `python monitor.py`
2. Dans un second terminal, lancer l'export : `python export.py`
3. Ouvrir `index.html` dans un navigateur.

Les machines surveillées se modifient dans la liste `HOSTS` de `monitor.py`.

## Pistes d'amélioration

- Alertes (e-mail ou Telegram) quand une machine tombe
- Surveillance de ports (TCP) en plus du ping
- Graphiques sur plusieurs jours

## Auteur

Zegrar Sofiane - Master 2 Réseaux et Télécommunications
