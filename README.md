# Imena — Rwanda Smart Business & Commerce Platform

An evolving local marketplace for Rwanda, built with React, TypeScript, Vite, Tailwind CSS, Python, Django REST Framework, and SQLite locally / PostgreSQL in production. The original requirements are preserved in [PROJECT_BRIEF.md](PROJECT_BRIEF.md).

## Start locally

Requirements: Python 3.11+, Node.js 20+, npm.

1. Start the Django API (PowerShell):

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   $env:DJANGO_SECRET_KEY = 'local-development-only-change-this'
   py manage.py migrate
   py manage.py seed_demo
   py manage.py runserver 8000
   ```

   The API is at `http://127.0.0.1:8000/api/`; Django admin is at `/admin/`. Create an administrator with `py manage.py createsuperuser`.

2. To open the ready-to-use browser preview without installing frontend packages, in a second terminal:

   ```powershell
   cd frontend
   python -m http.server 5173 --bind 127.0.0.1
   ```

   Open `http://127.0.0.1:5173/preview.html`. This preview loads the live Django product API and can place demo cash orders.

3. To run the React/Vite source instead, install frontend dependencies (requires access to npm's package registry) and start Vite:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open the printed Vite address, usually `http://localhost:5173`. Vite proxies `/api` to Django during development. The marketplace is also browseable without starting Django; cart contents are kept in local browser storage. Ordering requires the API.

## Current implementation

- Responsive marketplace and business-owner dashboard preview; English, Kinyarwanda, Kiswahili and French selector; voice-search graceful fallback; live product search/category filtering; saved finds; RWF cart and stock-aware order endpoint.
- Django REST models for businesses, memberships, verification records, categories, products, inventory movements, addresses, orders with immutable item snapshots, payments/refunds, services/bookings, reviews, favorites, notifications, conversations/messages, complaints and audit logs.
- Public discovery endpoints, token registration/login/current-user API, authenticated order history, guest order placement, server-calculated totals, row-level stock locks, and booking capacity conflict checks.
- Seed listings are explicitly demo data and are not verified businesses, real reviews, real orders or real sales. Business dashboard statistics are illustrative demo figures.
- Mobile Money choices create pending payment records only. Provider API initiation, authenticated callbacks, verification, refunds, outbound email/SMS/WhatsApp, and deployment credentials require provider configuration/merchant approval and are not live integrations. The webhook endpoint intentionally refuses payment status changes until a provider signature-verification adapter is configured.

## API

`GET /api/health/`, `GET /api/products/`, `GET /api/businesses/`, `GET /api/categories/`, `GET /api/services/`, and `GET /api/reviews/?business=<business-id>` provide public discovery. Businesses can be searched with `?search=` and filtered by `?district=`, `?category=`, and `?verified=true`; products support `?search=`, `?business=`, and `?available=true`. Service availability is checked with `GET /api/services/<id>/availability/?starts_at=<ISO-date>&ends_at=<ISO-date>&party_size=1`. Create cash orders with `POST /api/orders/` and reservations with `POST /api/bookings/`; both return references. Guests can track using `GET /api/orders/track/?reference=<reference>&phone=<checkout-phone>` or `/api/bookings/track/?reference=<reference>&phone=<booking-phone>`. Reviews require a signed-in customer and an order that includes the business and has reached `delivered`. Registration/login are at `POST /api/auth/register/` and `POST /api/auth/login/`; private endpoints accept `Authorization: Token <key>`. DRF browsable API is enabled for local development. Django admin at `/admin/` is the current administrator interface.

## Environment and production

Copy `.env.example`, set a strong unique `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=false`, configure `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL` with PostgreSQL, and restrict CORS to the deployed frontend. Run migrations, create a superuser, run `collectstatic`, serve HTTPS, configure durable media/document storage, backups, logs, and a real email provider. Keep payment credentials server-side. Review the production-readiness checklist in `docs/DEPLOYMENT.md` before launch.

## Payments and customer trust

Cash checkout is the only payment route that can complete through this local MVP. MTN MoMo/Airtel selections are architecture stubs and never mark an order paid. Demo businesses show pending verification and must not be treated as trusted sellers. Do not publish demonstration ratings or sales as genuine customer activity.
