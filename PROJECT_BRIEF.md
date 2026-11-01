# Rwanda Smart Business & Commerce Platform — Authoritative Project Brief

Keep this brief as the source of truth for the project. Preserve its requirements carefully as implementation progresses. Do not describe features as working, tested, deployed, or real unless they have actually been verified.

## 1. Project Overview

Act as a senior full-stack software engineer, UI/UX designer, database architect, cybersecurity specialist, and AI integration engineer. Develop a complete, modern, responsive, multilingual web application called **Rwanda Smart Business & Commerce Platform**. It must solve real problems faced by businesses, customers, hotels, restaurants, shops, tourism operators, and service providers in Rwanda. Transform static business websites and fragmented social-media commerce into one trusted, searchable, interactive, transaction-enabled digital marketplace.

This must be a functional website, not only a landing page, static template, or UI demonstration. Build a real backend, database, authentication, business dashboards, product management, bookings, order processing, payment integration architecture, and administrator controls. Design for deployment and real-world use in Rwanda.

## 2. Problems the System Must Solve

### A. Static Business Websites

Enable users to search and discover businesses; view business profiles, products, services, prices, and availability; place orders online; reserve hotel rooms, restaurant tables, and other bookable services; check stock; track order and booking status; contact businesses directly; and submit ratings and reviews after verified transactions.

### B. Fragmented Informal Commerce

Create a central searchable marketplace where verified businesses can register, publish products and services, manage orders, and communicate with customers. Include business registration and verification; category and location discovery; search, filtering, and sorting; product and service listings; seller contact information; customer inquiries and messaging; order history and transaction records; customer reviews; and reporting mechanisms.

### C. Language and Literacy Barriers

Support English, Kinyarwanda, Kiswahili, and French. Users can change language at any time. Translate navigation, forms, buttons, notifications, order statuses, validation messages, and dashboards. Use simple language, large readable text, clear icons, visual instructions, and mobile-friendly navigation. Include optional text-to-speech, speech-to-text, and voice-assisted search where supported, with graceful browser capability fallbacks. Do not rely exclusively on English or complex technical terminology.

### D. E-commerce Checkout and Mobile Money

Provide straightforward mobile checkout with cash on delivery or cash payment when seller-enabled, and Mobile Money integration through legitimate providers. Make providers configurable, including MTN MoMo and Airtel Money, subject to API availability and merchant approval. Include payment status tracking, transaction references, receipts and confirmations, failed-payment handling, and refund status management. Verify payments server-side through trusted provider responses/callbacks/webhooks. Never mark a transaction paid because a customer clicked a button or entered a reference. Use sandbox credentials in development and never put secret API keys in frontend code.

## 3. Main Website Pages

### 3.1 Home Page

Include platform logo/name, language selector, search for products/services/businesses, Rwanda location selector, main navigation, featured verified businesses, popular products/services, nearby businesses when location permissions are granted, hotels/restaurants/shops/tourism/transport/professional services categories, special offers, recently added businesses, testimonials based on genuine reviews, calls to action for customers and business owners, and footer contact/help/terms/privacy/social links. Load business and product information dynamically from the database.

### 3.2 Business Directory

Browse and search by business name, category, district/city/sector, products/services, price range, availability, verification status, and customer rating. Include pagination or infinite scrolling, empty results, and loading states.

### 3.3 Business Profile Page

Each business has a public profile with business name/logo, cover image, description, address/location, contact details, opening hours, verification status, products/services, prices/availability, booking options where relevant, reviews/ratings, delivery options, accepted payment methods, and contact/inquiry functionality.

### 3.4 Product Marketplace

Products contain name, description, images, category, price in Rwandan francs (RWF), available stock, seller, delivery/pickup options, product status, and availability indicator. Customers can add items to cart, update quantities, remove products, calculate totals, and check out. Validate stock on the server before accepting orders and prevent overselling under concurrent purchases.

### 3.5 Service Booking System

Reusable bookings for hotels/guesthouses, restaurants, salons/barbershops, tour operators, repair/maintenance, and professional services. Customers choose service, date, time, number of people where relevant, and additional requirements. Check availability before confirmation; prevent overlapping reservations where capacity is limited. Generate booking references and let customers/business owners view booking status.

### 3.6 Shopping Cart and Checkout

Collect customer information; delivery or pickup selection; delivery address when applicable; order summary; item subtotal; delivery fee; discounts; total in RWF; payment method; and confirmation. Calculate totals on the server and do not trust browser-supplied prices or totals. Support guest checkout if configured and registered customer accounts.

### 3.7 Customer Dashboard

Customers can register/log in, edit profiles, save delivery addresses, view current/previous orders, track statuses, view bookings and cancellation policies, view payment/refund statuses, save favorite businesses/products, submit reviews for eligible completed transactions, contact businesses, and manage language/notification preferences.

### 3.8 Business Owner Dashboard

Business owners can create/manage profiles; securely submit verification documents; add/edit/archive products and services; upload product images; update prices/stock; manage incoming orders; accept/reject with reason; update fulfillment/delivery statuses; manage bookings/availability; view inquiries; configure supported payment methods; review transaction records; view daily/weekly/monthly sales reports; export permitted reports to CSV; and manage employees/permissions where applicable. Only authorized owners/staff may access their own business data.

### 3.9 Administrator Dashboard

Protected administration panel to manage users/business accounts; verify/reject business applications; review uploaded verification documents; manage categories/locations; moderate products/services; review reports and suspicious activity; handle complaints; monitor orders/bookings/payment statuses; suspend policy-violating accounts; manage translations/platform settings; view statistics/audit logs. Use role-based permissions and record important administrative actions.

### 3.10 Communication and Notifications

In-app notifications for new orders, order acceptance/rejection, booking confirmation/cancellation, payment confirmation/failure, shipment/delivery updates, and business verification results. Add email when configured. Design optional SMS/WhatsApp Business integration points using official APIs and appropriate consent. Do not pretend a message was sent if the provider is not configured.

### 3.11 Reviews and Trust

Include verified business badges, verified-purchase reviews where applicable, star ratings, complaint reporting, review moderation, verification status, and clear policies against fraudulent reviews/misleading listings. Never fabricate reviews, customer counts, transactions, or verification badges.

## 4. Technology Stack

Use unless a technical constraint requires a documented alternative.

- Frontend: React with Vite, TypeScript, Tailwind CSS, React Router, reusable components.
- Backend: Python, Django, Django REST Framework, Django authentication and permission controls.
- Database: PostgreSQL in production; SQLite may be used for local development when appropriate.
- Also: Django migrations, secure image/document storage, environment variables, automated tests, Git/GitHub, Render or compatible hosting.
- Single Git repository with separate frontend and backend directories.

## 5. Suggested Project Structure

```text
rwanda-smart-commerce/
  frontend/src/{components,pages,layouts,services,hooks,contexts,translations,types,assets}/
  backend/{config,accounts,businesses,catalog,orders,bookings,payments,reviews,notifications,analytics}/
  backend/manage.py
  backend/tests/
  docs/
  .gitignore
  README.md
  .env.example
```

## 6. Database Design

Design a normalized relational database with relationships, indexes, constraints, and timestamps. Include User, UserProfile, Business, BusinessMembership, BusinessVerification, Category, Product, ProductImage, InventoryMovement, ShoppingCart, CartItem, Order, OrderItem, Payment, Refund, Booking, Service, BusinessAvailability, Address, Review, Favorite, Notification, Conversation, Message, Complaint, and AuditLog. Use UUIDs or suitable identifiers, database constraints, decimal money fields, and timezone-aware timestamps. Store prices/transaction amounts as decimal values, never binary floating point. Keep product name, unit price, and quantity as immutable order transaction snapshots. Define explicit state transitions for orders, bookings, and payments.

## 7. Authentication and Security

Implement registration/login, secure password hashing, logout, password reset, email verification where configured, role-based access control, object-level permission checks, CSRF where applicable, restricted CORS, input validation, sensitive-endpoint rate limiting, secure upload validation, common web vulnerability protection, HTTPS in production, and audit logs for sensitive operations. Never commit passwords, secret keys, production credentials, or payment secrets. `.env.example` contains placeholders only.

## 8. API Requirements

Document REST endpoints for authentication/profiles; business registration/verification/discovery; product/category management; search/filtering; cart; order creation/tracking; inventory; booking; payment initiation/status verification; refund requests; reviews/complaints; notifications; reports; and administration. Use correct HTTP methods/status codes and validate permissions/data server-side. Document using OpenAPI or equivalent.

## 9. Real Mobile Money Integration

Implement a provider abstraction so providers can be added without rewriting the application. Workflow: create pending order/payment attempt; validate order/amount server-side; initiate through configured provider; store provider transaction reference; receive and validate callbacks; verify through trusted provider API where required; update payment/order safely; prevent duplicate callback processing; reconcile uncertain outcomes; generate receipt after confirmed payment. Use idempotency and secure webhook validation. If live credentials are unavailable, clearly label sandbox/simulated payment mode and never represent simulation as real Mobile Money.

## 10. AI and Accessibility Features

Optional useful AI features: natural-language product/business search, multilingual support, voice navigation, recommendations, listing categorization suggestions, business report summaries, FAQs. Use configurable backend AI provider credentials and functional non-AI fallback. AI cannot approve payments, change verified financial records, or bypass administrator permissions. The platform remains usable without voice recognition, AI, or GPS.

## 11. User Interface and Design

Professional African commerce brand: clean white/light background, deep navy or dark green primary colors, green success accents, high contrast, clear product cards, consistent buttons/forms, mobile-first responsive layout, accessible navigation and keyboard controls, clear loading/success/error/empty states, smartphone/tablet/laptop/desktop support. Use real imagery or clearly labeled placeholders; avoid excessive animation/clutter. Include mobile navigation, accessible language selector, search suggestions, clear calls to action.

## 12. Testing and Quality Assurance

Create automated tests for registration/login, role/ownership permissions, business verification, product creation/editing, stock validation, cart calculations, order creation/transitions, booking availability/conflicts, payment callback verification, duplicate payment notifications, reviews/moderation, multilingual interface behavior, and API errors. Test invalid input, unauthorized requests, insufficient stock, duplicate submissions, failed payments, concurrent order attempts. Run migrations and tests before declaring complete.

## 13. Deployment and Documentation

Prepare production deployment with frontend build configuration, backend deployment configuration, PostgreSQL, static/media handling, environment-variable documentation, migration instructions, superuser instructions, API documentation, complete local setup README, selected-host deployment guide, backup/recovery guidance, and basic monitoring/error logging. Start locally with documented commands and no hidden-file or undocumented manual dependencies.

## 14. Required Deliverables

Complete frontend and backend source; models and migrations; REST API; authentication/authorization; functional customer/business/admin dashboards; marketplace/search; working cart/order processing; booking/availability; Mobile Money integration architecture; English/Kinyarwanda/Kiswahili/French; accessible responsive UI; automated tests; `.env.example`; README/deployment docs; clearly labeled demo seed businesses/products; Git repository setup instructions; production-readiness checklist.

## 15. Development Instructions

Build in logical stages and continue beyond a homepage or sample components:

1. Repository, frontend, backend, database.
2. Authentication, profiles, permissions.
3. Business registration, verification, directory search.
4. Products, categories, stock, inventory.
5. Cart, checkout, orders, history.
6. Service availability and bookings.
7. Payment-provider integration and sandbox testing.
8. Multilingual UI, accessibility, notifications, AI features.
9. Analytics, administration, security controls, audit logs.
10. Tests, fixes, documentation, deployment.

Clearly identify features requiring third-party credentials, business approval, or external configuration. When a development environment is available, create actual files, install dependencies, run migrations/tests, and fix errors. Otherwise give complete file contents and exact commands in manageable stages. Do not claim deployment, real payments, working APIs, or passing tests unless verified.
