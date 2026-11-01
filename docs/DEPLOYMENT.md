# Deployment and readiness notes

## Hosting outline (Render-compatible)

Use a PostgreSQL instance plus a Python web service rooted at `backend/`. Install `requirements.txt`; start with `gunicorn config.wsgi:application` (add `gunicorn` to production requirements); build frontend with `npm ci && npm run build`; publish `frontend/dist` through a static site or same-origin reverse proxy. Configure `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` in the host environment. Run `python manage.py migrate` and `python manage.py collectstatic --noinput` on deploy. Configure TLS and health check `/api/health/`.

## Production readiness checklist

- [ ] Create business-owner and customer onboarding flows, email verification, password reset and account recovery.
- [ ] Obtain approval for MTN MoMo/Airtel merchant accounts; implement provider-specific initiation, signed callbacks, status reconciliation, idempotency, refunds and receipt delivery. Do not treat the current stub as a live payment integration.
- [ ] Configure object storage, private document access, upload malware/type/size checks, retention rules and backups.
- [ ] Complete business-scoped owner/staff product, booking and order-management APIs; add admin review workflows and audit events.
- [ ] Complete frontend API integration for discovery, customer dashboard, product editing, checkout, booking and admin moderation.
- [ ] Verify guest contact, delivery-fee, tax, cancellation/refund and seller policies for Rwanda operations.
- [ ] Restrict CORS/hosts, strong secrets, HTTPS, rate limits, secure cookies, monitoring, error reporting and database restore drills.
- [ ] Run migrations and the automated security, permission, concurrency, payment callback, translation, and responsive UI test suite before launch.
- [ ] Replace all explicitly labeled sample dashboard figures and demo listings before public use.

SQLite is suitable for local development. PostgreSQL is required for deployment and is important for reliable concurrent inventory locks. Keep all credentials outside version control. Back up PostgreSQL daily and test restoring into a separate environment. Provider callbacks require a valid provider signature before a payment state can transition.
