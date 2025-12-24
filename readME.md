# SneakPeek  
### Online Sneaker Bidding & Auction Platform

SneakPeek is a web-based sneaker marketplace where users can **buy and sell sneakers through auctions**.  
The system is designed with a clear separation of roles — **buyers**, **sellers**, and **admins** — and follows a scalable architecture suitable for future expansion.

>  Advanced auction mechanisms (Vickrey Auction) will be implemented in later phases.

---

## Features

### User Roles
- **Buyer**
  - Browse sneaker listings
  - Place bids on live auctions
  - Track active, winning, and past bids
- **Seller**
  - Create sneaker listings
  - Configure auction parameters (time, starting bid, etc.)
  - Manage listings and bids *(planned)*
- **Admin** *(planned)*
  - Moderate users and listings
  - Monitor auctions
  - Platform analytics

---

### Core Functionalities
- User authentication (Login / Signup)
- Role selection during signup (Buyer / Seller)
- Marketplace with sneaker listings
- Auction-based bidding system
- Responsive UI (desktop & mobile)
- Seller dashboard *(planned)*

---

## Auction System

### Current Phase
- Standard auction model (open bidding)
- Time-based auction closing

### Planned Upgrade
#### Vickrey Auction (Second-Price Sealed-Bid Auction)
- Bidders submit sealed bids
- Highest bidder wins
- Winner pays the **second-highest bid**
- Encourages truthful bidding
- Research-backed auction mechanism

---

## Tech Stack

### Frontend
- HTML5
- CSS3 (Custom design system)
- Vanilla JavaScript

### Backend
- Django (Python)
- Django Templates
- Django Authentication

### Database
- SQLite (development)
- PostgreSQL *(planned)*

---

## Project Structure

```text
firstproject/
├── sneakpeek/
│   ├── templates/
│   │   └── sneakpeek/
│   │       ├── base.html
│   │       ├── home.html
│   │       ├── marketplace.html
│   │       ├── sell.html
│   │       ├── bids.html
│   │       └── auth/
│   │           ├── login.html
│   │           └── signup.html
│   ├── static/
│   │   └── sneakpeek/
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           └── main.js
│   ├── views.py
│   ├── urls.py
│   └── models.py
├── firstproject/
│   └── settings.py
├── manage.py
└── README.md