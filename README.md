#  FootBook

**FootBook** is a web application for amateur football players and pitch owners. It solves two common problems: how hard it is to book a pitch quickly, and how hard it is to find enough players to complete a team.

> Academic project – Software Engineering (S3), Mohammed V University of Rabat.
> Supervised by Pr. Retbi.

##  Overview

FootBook lets players search for available pitches, book a time slot, and receive a **unique QR code** as proof of booking. Pitch owners can then validate bookings on site by scanning (or manually entering) that code. If a team is short of players, a player can post an **announcement** linked to their booking so others can join the match.

##  Features

###  Authentication & roles
- Sign up and log in with username and password (Django session authentication, hashed passwords)
- Two roles with separate interfaces: **Player** and **Pitch Owner**
- Basic profile management

###  Pitch search
- Browse available pitches (name, address, price, category)
- Filter by category, price range, and area
- Detailed pitch page with available time slots

###  Booking & QR code
- Select an available slot (double-booking is prevented)
- Unique QR code generated for each confirmed booking
- Booking history for each player

###  Pitch owner dashboard
- View upcoming bookings for their pitches
- Validate a booking by QR scan or manual code entry (a QR code can only be validated once)
- See booker details for each reservation

###  Player announcements
- Create an announcement tied to an existing booking, specifying the number of missing players
- Browse announcements and join a match

###  Player profile
- Simple profile showing name and number of matches played (updated automatically on validated participation)

##  Tech Stack

| Component        | Technology                                   |
|------------------|----------------------------------------------|
| Backend + pages  | Django 5.1 (server-rendered templates)       |
| Frontend         | Django templates + Bootstrap 5.3             |
| Database         | SQLite (MVP)                                  |
| QR codes         | `qrcode` (SVG) ; scan with `html5-qrcode`     |
| Authentication   | Django sessions, role-based access (403)     |
| Deployment       | PythonAnywhere                               |

##  Data Model

- **User** – id, name, email, password, role (player / owner)
- **Terrain** – id, owner_id, name, category, price, zone, address
- **Reservation** – id, terrain_id, user_id, date, time, status, qr_code
- **Annonce** – id, reservation_id, missing_players, description
- **Participation** – id, announcement_id, user_id

##  MVP Success Criteria

- A player can sign up, search for a pitch, book it, and receive a QR code
- An owner can view their bookings and validate a QR code
- A player can create an announcement and another player can join it
- The app is deployed and reachable via a public URL

##  Roadmap (6 weeks)

| Week | Deliverable |
|------|-------------|
| 1 | Project setup, data modeling, authentication |
| 2 | Pitch management (CRUD) and search filters |
| 3 | Booking system and QR code generation |
| 4 | Owner interface and QR validation |
| 5 | Announcements and player profile |
| 6 | Testing, bug fixes, deployment |

##  Non-Functional Goals

- **Usability:** simple, mobile-friendly interface
- **Performance:** response time under 2 seconds for common actions
- **Security:** hashed passwords, role-based access control
- **Reliability:** each QR code is single-use
- **Portability:** runs in any browser, no installation needed

##  Conception
- Maquettes et diagramme de classes (Figma) : https://www.figma.com/design/hEv9ifxAFM3uYmsss0s1zu
- Fichiers de conception dans `docs/conception/`

##  Getting Started

```bash
git clone https://github.com/3xploitur4/FootBook.git
cd FootBook/Django
python -m venv venv && source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py charger_demo      # comptes proprio1, proprio2, joueur1..3 (mot de passe : footbook2026)
python manage.py runserver         # http://127.0.0.1:8000
python manage.py test              # 69 tests (sprints 1 à 4)
```

Voir `Django/README.md` pour le détail.

## 👥 Authors

- **Achraf Charkam**
- **Ali Mejjat**

Supervised by **Pr. Retbi** – Université Mohammed V de Rabat
