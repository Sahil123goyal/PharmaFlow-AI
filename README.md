# PharmaFlowAI

Pharmacy retail management system for a small independent pharmacy.

> **Current iteration: authentication only.**
> This repository contains the Django foundation and the Owner/Admin **login
> page**. The dashboard, medicine catalogue, batch inventory, billing,
> suppliers, customers, analytics, alerts and chatbot are planned for later
> iterations and are **not** implemented yet.

Course project for **UCS503P**, Thapar Institute of Engineering and Technology.

---

## Table of contents

- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Creating a user](#creating-a-user)
- [URLs](#urls)
- [How the login flow works](#how-the-login-flow-works)
- [Project structure](#project-structure)
- [Running the tests](#running-the-tests)
- [Switching to PostgreSQL](#switching-to-postgresql)
- [Configuration reference](#configuration-reference)
- [Deployment checklist](#deployment-checklist)
- [Not implemented yet](#not-implemented-yet)

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.13, Django 6.1 |
| Frontend | Django Templates, hand-written CSS, vanilla JavaScript |
| Database | PostgreSQL (production target) · SQLite (local default) |
| Authentication | Django built-in session authentication, custom user model |
| Tests | Django test framework |

No frontend framework and no CSS framework are used — the styling is a small
token-based design system in `static/css/`.

---

## Quick start

### 1. Install dependencies

```bash
py -3.13 -m pip install -r requirements.txt
```

A virtual environment is recommended:

```bash
py -3.13 -m venv .venv && source .venv/Scripts/activate && pip install -r requirements.txt
```

### 2. Configure the environment (optional)

The project runs with sensible development defaults. To customise, copy the
template and edit it:

```bash
cp .env.example .env
```

Without a `.env`, the project runs with `DEBUG=True` on a local SQLite database.

### 3. Apply migrations

```bash
py -3.13 manage.py migrate
```

### 4. Run the server

```bash
py -3.13 manage.py runserver
```

### 5. Open the login page

<http://127.0.0.1:8000/accounts/login/>

Visiting <http://127.0.0.1:8000/> redirects there automatically when you are
signed out.

---

## Creating a user

Sign-in requires an account — there is no public self-registration, because a
pharmacy owner creates the accounts.

### Interactive (recommended)

```bash
py -3.13 manage.py createsuperuser
```

You will be prompted for a username, an email address (required and unique) and
a password.

### Non-interactive

```bash
DJANGO_SUPERUSER_PASSWORD='ChooseAStrongPassword' py -3.13 manage.py createsuperuser --noinput --username owner --email owner@pharmacy.com
```

### Resetting a password

Self-service password recovery is deliberately not implemented in this
iteration. Reset from the command line:

```bash
py -3.13 manage.py changepassword owner
```

…or from the Django admin at <http://127.0.0.1:8000/admin/>.

### Accounts created during development

| Username | Email | Role |
| --- | --- | --- |
| `owner` | `owner@pharmacy.com` | Owner / Admin |
| `sahil` | `goyal@gmail.com` | Owner / Admin |

These live only in your local `db.sqlite3`, which is git-ignored. Change or
delete them freely — and never reuse these passwords anywhere real.

---

## URLs

| URL | Purpose |
| --- | --- |
| `/` | Redirects to the dashboard when signed in, otherwise to login |
| `/accounts/login/` | **The login page** |
| `/accounts/logout/` | Sign out (POST only) |
| `/accounts/password-help/` | Static guidance for the "Forgot password?" link |
| `/dashboard/` | Placeholder landing page — proves auth works, no features yet |
| `/admin/` | Django admin, for user management and password resets |

---

## How the login flow works

1. **GET `/accounts/login/`** — `PharmacyLoginView` (a subclass of Django's
   `LoginView`) renders `templates/accounts/login.html` with
   `PharmacyLoginForm`. If you are already signed in, it redirects straight to
   `/dashboard/`.

2. **Client-side checks** (`static/js/login.js`) — on submit, empty fields are
   blocked, a malformed email is flagged, the first invalid field is focused and
   a summary alert appears. The button then enters a loading state
   ("Signing in…" plus a spinner) and further submits are ignored, preventing
   double posts. This layer is progressive enhancement only: with JavaScript
   disabled the form still posts and Django performs the same validation.

3. **POST `/accounts/login/`** — CSRF is enforced by
   `CsrfViewMiddleware`. `PharmacyLoginForm` (extending Django's
   `AuthenticationForm`) validates the fields, then calls `authenticate()`.

4. **Credential lookup** — `EmailOrUsernameModelBackend` matches the submitted
   identifier against **either** the username **or** the email address,
   case-insensitively, so the owner can type whichever they remember. Password
   hashing, `is_active` handling and permission checks are inherited from
   Django's `ModelBackend`.

5. **On failure** — the form re-renders with a single generic message: *"The
   email/username or password you entered is incorrect."* The message is
   identical for a wrong password, an unknown account and a deactivated account,
   so the page never reveals which accounts exist. The attempt is logged as a
   warning.

6. **On success** — Django creates the session and cycles the session key
   (guarding against session fixation). `remember_me` then sets the lifetime:

   | "Remember me" | Session lifetime |
   | --- | --- |
   | Ticked | `SESSION_COOKIE_AGE` — 14 days by default |
   | Unticked | Expires when the browser closes (`set_expiry(0)`) |

7. **Redirect** — to `?next=` when it is a safe same-host URL (Django rejects
   external URLs), otherwise to `settings.LOGIN_REDIRECT_URL`, which is
   `/dashboard/`.

8. **Sign out** — POST to `/accounts/logout/` flushes the session and returns to
   the login page with a "You have been signed out." confirmation. GET is
   rejected with `405`, so a stray link cannot log anyone out.

---

## Project structure

```
G:\Claude_pharma
├── manage.py
├── requirements.txt
├── .env.example                    # environment template
│
├── config/                         # project configuration
│   ├── settings.py                 # environment-driven settings
│   ├── urls.py                     # root URL routing
│   ├── wsgi.py / asgi.py
│
├── apps/                           # feature modules
│   ├── accounts/                   # authentication (this iteration)
│   │   ├── models.py               # custom User model with pharmacy Role
│   │   ├── backends.py             # email-or-username auth backend
│   │   ├── forms.py                # login form + "Remember me"
│   │   ├── views.py                # login / logout / password help
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── migrations/
│   │   └── tests/test_login.py     # 18 tests
│   │
│   └── core/                       # shared plumbing
│       ├── views.py                # root redirect + dashboard placeholder
│       ├── urls.py
│       ├── context_processors.py   # product name and tagline
│       └── templatetags/
│           └── form_extras.py      # ARIA-aware field rendering
│
├── templates/
│   ├── base.html                   # HTML shell
│   ├── accounts/
│   │   ├── login.html              # the login page
│   │   └── password_help.html
│   ├── core/
│   │   └── dashboard_placeholder.html
│   └── partials/
│       ├── _logo.html              # reusable logo mark
│       └── _auth_decor.html        # decorative healthcare motif
│
└── static/
    ├── css/
    │   ├── tokens.css              # design tokens — colour, type, spacing
    │   ├── base.css                # buttons, fields, alerts, cards
    │   ├── auth.css                # authentication layout
    │   └── placeholder.css         # temporary; delete with the stub
    ├── js/
    │   └── login.js                # validation, loading state, toggle
    └── img/favicon.svg
```

### Design notes

- **Separation of concerns** — templates hold no styling, CSS holds no content,
  JavaScript is behaviour-only, and all authentication logic lives in
  `apps/accounts/`.
- **Design tokens** — every colour, size and shadow is a CSS variable in
  `tokens.css`, so later modules inherit the same visual language.
- **Custom user model from day one** — swapping `AUTH_USER_MODEL` after tables
  exist is painful, so `accounts.User` is in place already, with a `role` field
  ready for staff accounts.
- **Accessibility** — labelled inputs, `aria-invalid` and `aria-describedby` on
  errors, an `aria-live` message region, visible focus rings, 46 px touch
  targets and `prefers-reduced-motion` support.

---

## Running the tests

```bash
py -3.13 manage.py test apps
```

18 tests cover page rendering, login by username and by email, wrong passwords,
unknown accounts, deactivated accounts, empty-field validation, both
"Remember me" session modes, `next` redirect safety (including rejection of
external URLs), logout behaviour and access control on `/dashboard/`.

---

## Switching to PostgreSQL

PostgreSQL is the target database from the proposal. The project uses it as soon
as `POSTGRES_DB` is set; otherwise it falls back to SQLite so a fresh clone runs
with no setup.

1. Create the database:

   ```bash
   createdb pharmaflowai
   ```

2. Set the variables in `.env`:

   ```
   POSTGRES_DB=pharmaflowai
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your-password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

3. Migrate:

   ```bash
   py -3.13 manage.py migrate
   ```

The `psycopg[binary]` driver in `requirements.txt` is only needed for this path.

---

## Configuration reference

Every setting is read from the environment, seeded from `.env` when present.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `True` | Debug mode. Set `False` outside local development |
| `DJANGO_SECRET_KEY` | insecure dev key | **Must** be set outside development |
| `DJANGO_ALLOWED_HOSTS` | localhost values | Comma-separated allowed hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Comma-separated trusted origins |
| `DJANGO_TIME_ZONE` | `Asia/Kolkata` | Store time zone |
| `DJANGO_LOG_LEVEL` | `INFO` | Root log level |
| `SESSION_COOKIE_AGE` | `1209600` | "Remember me" lifetime, in seconds |
| `POSTGRES_*` | unset | Set `POSTGRES_DB` to switch off SQLite |
| `EMAIL_*` | unset | SMTP settings, used only when `DEBUG=False` |

With `DEBUG=False`, the settings module automatically enables HTTPS redirects,
secure and HTTP-only cookies, HSTS, `X-Frame-Options: DENY` and content-type
nosniff.

---

## Deployment checklist

Verify the production configuration before deploying:

```bash
py -3.13 manage.py check --deploy
```

This passes cleanly with `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`,
`DJANGO_ALLOWED_HOSTS` and `EMAIL_HOST` set. Also run:

```bash
py -3.13 manage.py collectstatic
```

Outside `DEBUG`, static files are served through `ManifestStaticFilesStorage`
(hashed filenames), so `collectstatic` is required.

---

## Not implemented yet

Deliberately out of scope for this iteration, in roughly planned order:

- Owner dashboard with store summaries
- Medicine catalogue (create, view, update, deactivate)
- Batch-level inventory with quantity, prices and expiry
- Stock movement records
- Supplier management and purchase history
- Customer retail records
- Billing and sales, with automatic batch stock deduction (FEFO)
- Low-stock and expiry alerts
- Sales and inventory analytics
- Email-based password recovery
- Machine learning demand forecasting
- AI chatbot over store data

The `/dashboard/` page is a placeholder that only confirms authentication
works. `static/css/placeholder.css` and
`templates/core/dashboard_placeholder.html` should be deleted when the real
dashboard is built.
