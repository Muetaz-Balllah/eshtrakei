# Eshtrakei — Implementation Plan

Internet subscription marketplace: one client account, many internet companies, one manager per company, and one platform admin over the whole platform.

This document is the build plan only. Implementation follows the phases in order. Each phase ends with a stop. The next phase starts only after you confirm that the current phase succeeded.

The website UI is Arabic and RTL. This plan is English.

---

## 1. Project summary and roles

Eshtrakei is one website where a client picks a registered internet company, sees only that company’s packages, and subscribes. The same client account can hold subscriptions with more than one company. Each company is operated by exactly one company manager, who sees only that company’s packages, coupons, clients, subscriptions, sales, and complaints. The platform admin supervises the platform and does not manage any company’s packages, coupons, or clients.

There are three roles and no others.

| Role | Arabic UI name | How the account is created | Responsibility |
| --- | --- | --- | --- |
| Platform Admin | مدير المنصة | Seed script. Credentials are given to you when Phase 0 is handed over. | Approve or reject company join requests. Monitor platform-wide performance. Suspend or stop a company that violates the terms. Manage general platform settings. Follow complaints directed at the platform. Create each company manager account inside the platform. |
| Company Manager | موظف الشركة | Created by the Platform Admin inside the platform. No public signup and no seed script. | One manager per company. Own-company dashboard only. Package create/update/delete. Create that company’s coupons. Follow that company’s clients and subscriptions. Activate, renew, review, and stop those subscriptions. Follow that company’s sales and profits. Reply to complaints directed at that company. |
| Client | الزبون | Self-registration on the website. The only role that may register itself. | Register and log in. Choose a company. Browse that company’s packages. Buy a new subscription or renew an existing one. Apply a discount coupon when one is available. See current subscription status and days remaining. See subscription history across companies. Receive a confirmation email and a PDF invoice after each purchase. Receive a notification when a subscription is close to ending. Submit a complaint or a technical-support request, either to a company the client deals with or to the platform. Switch the interface between light and dark. |

### How manager accounts fit company approval

These are two separate admin duties:

1. **Join decision.** The Platform Admin approves or rejects a company’s request to join. An approved company may appear to clients as an available company. A rejected request does not produce an operating company.
2. **Manager account.** The person who operates an approved company is a Company Manager. The Platform Admin creates that user inside the platform and attaches that user to exactly one company. The manager does not register on the public site, and the manager is not created in the seed script.

A manager account is created only for a company the admin has approved. Rejection does not create a manager.

The description requires both duties. It does not say who submits a join request or on which screen. That intake is Open Question 1. Until you answer it, the plan does not add a public “join as a company” form, an email intake, or an admin-typed application. Phase 2 still builds companies, the one-manager rule, admin creation of the manager, and suspend/stop, because those are specified. The approve/reject screen is part of Phase 2 and is wired to a real intake only after Open Question 1 is answered.

### Scope boundary

The phases below are the whole product. In particular, the build includes purchase confirmation email, the PDF invoice, the expiry notification, coupons, complaints, technical-support requests, light/dark mode, and the three roles’ duties listed above.

Adjacent products that the description does not mention are outside the phases: password reset, profile editing, a second manager for the same company, public company self-registration, card collection, a second payment provider, tax lines, ratings, chat, search, CSV export, and a second UI language.

---

## 2. Features in implementation order

Work is feature by feature. For each feature the order inside the phase is: backend, then frontend, then a joint checklist, then a stop.

| Phase | Feature | Why it is here |
| --- | --- | --- |
| 0 | Foundation | Folders, configuration, SQLite, Redis token store, JWT login/logout, role checks, Platform Admin seed, Arabic RTL shell, light/dark toggle. Every later phase depends on this. |
| 1 | Client registration | Completes `auth`. Clients are the only self-registered role. Later client screens need a client session. |
| 2 | Companies | The company is the isolation boundary. Packages, coupons, subscriptions, invoices, and company complaints all belong to a company. Manager accounts are created here. |
| 3 | Packages | A subscription points at a package. Clients can browse only after packages exist. |
| 4 | Coupons | Coupons belong to one company and are applied when that company’s package is purchased. The coupon must exist before checkout. |
| 5 | Payments | Checkout calls an abstract provider. The mock provider is in place before any subscription is created, so the rest of the system never talks to a concrete provider. |
| 6 | Subscriptions | Purchase, renewal, history, days remaining, and the manager’s client and subscription tools. Uses companies, packages, coupons, and the payment provider. |
| 7 | Invoices and purchase email | The description places a PDF invoice and a confirmation email immediately after a successful purchase. They are the next step on that same success path. |
| 8 | Expiry notifications | Needs subscriptions that already have an end date. |
| 9 | Complaints and technical support | Needs clients, companies, and the rule for which company a client may address. |
| 10 | Company sales and profits | Needs successful purchases as the sales data. |
| 11 | Platform performance | Needs companies plus the aggregate of their activity. The admin sees totals across companies and does not open another company’s private dashboard. |
| 12 | Platform settings | General settings do not block the other features. The concrete setting keys are Open Question 11. |

Light/dark mode is a client-facing requirement and a property of the whole website. It is built once, in the Phase 0 shell, and every later screen uses it.

Company-dashboard navigation is created in Phase 2. Later phases add only that phase’s pages inside the same shell.

---

## 3. Database design

PostgreSQL is the production target. Development uses SQLite. The schema uses only types and constraints that both accept. Table and column names are English. User-visible strings are Arabic in the UI and in generated email and PDF text.

Primary keys are integers. Money is `Numeric(12, 2)`, never floating point. Timestamps are timezone-aware UTC. Enums are stored as strings.

SQLite foreign keys are easy to leave off. `db.py` runs `PRAGMA foreign_keys=ON` on every SQLite connection.

### 3.1 Tables

**users**

| Column | Notes |
| --- | --- |
| id | Primary key |
| full_name | Required for the invoice “client data” and for the manager’s name |
| email | Unique, used as the login identifier and as the purchase-confirmation address |
| password_hash | Hash only |
| role | `platform_admin`, `company_manager`, or `client` |
| is_active | Login fails when this is false |
| created_at | |

Extra client registration fields are Open Question 12. They are not added unless you name them.

**companies**

| Column | Notes |
| --- | --- |
| id | Primary key |
| name | The name the client sees in the company list |
| status | See statuses below |
| created_at | |
| updated_at | |

The description guarantees a company name. Logo, description, phone, and coverage area are Open Question 14. They are not columns until you ask for them.

**company_managers**

| Column | Notes |
| --- | --- |
| id | Primary key |
| user_id | Unique, foreign key to `users`. One company per manager. |
| company_id | Unique, foreign key to `companies`. One manager per company. |
| created_at | |

**company_join_requests**

| Column | Notes |
| --- | --- |
| id | Primary key |
| status | `pending`, `approved`, or `rejected` |
| company_id | Nullable until an approval creates or links the company |
| reviewed_by | Nullable foreign key to the Platform Admin user |
| reviewed_at | Nullable |
| created_at | |

The columns that describe the submitted application are Open Question 1. The table exists because approve/reject needs a record to decide on. No intake writer is added until that question is answered.

**packages**

| Column | Notes |
| --- | --- |
| id | Primary key |
| company_id | Foreign key to `companies`. A package belongs to one company. |
| name | |
| price | Numeric |
| duration_amount | Integer. The subscription length used to compute the end date. |
| duration_unit | Values come from Open Question 3. |
| data_allowance | Display value for الحجم. Shape comes from Open Question 3. |
| speed | Display value for السرعة. Shape comes from Open Question 3. |
| created_at | |
| updated_at | |

**coupons**

| Column | Notes |
| --- | --- |
| id | Primary key |
| company_id | Foreign key. A coupon works only for this company. |
| code | Unique together with `company_id`. The same code may exist at another company. |
| created_at | |

Discount type, discount value, expiry, and usage limits are Open Question 4. Those columns are added when you answer it. Until then the table is not migrated and Phase 4 does not start. The description asks for creation of coupons, so the manager can create and list them. It does not ask for coupon edit or coupon delete, so those actions are not in the API.

**subscriptions**

| Column | Notes |
| --- | --- |
| id | Primary key |
| client_id | Foreign key to `users` |
| company_id | Foreign key to `companies` |
| package_id | Foreign key to `packages` |
| start_date | Date |
| end_date | Date |
| status | `active` or `expired`, the two states named in the data-model section |
| package_name_snapshot | Copy of the package at purchase time |
| price_snapshot | |
| duration_snapshot | |
| data_allowance_snapshot | |
| speed_snapshot | |
| created_at | |

Snapshots stay on the subscription so a later package edit does not rewrite a subscription the client already bought. The invoice is generated from the same snapshot.

A client may hold active subscriptions with different companies, because one account deals with more than one company. Whether two active subscriptions may exist for the same client and the same company is Open Question 5.

**payments**

| Column | Notes |
| --- | --- |
| id | Primary key |
| client_id | |
| company_id | |
| package_id | |
| subscription_id | Null on a failed attempt. Set when success creates or extends a subscription (extension rule is Open Question 5). |
| coupon_id | Nullable |
| amount | Amount after the coupon rule, once that rule exists |
| currency | Code from configuration, Open Question 7 |
| provider | Provider name, `mock` for the built-in provider |
| status | `succeeded` or `failed` |
| provider_reference | Id returned by the provider. For the mock, a generated reference. |
| failure_code | Nullable. A short code such as `mock_declined`. |
| idempotency_key | Unique |
| created_at | |

There is no column for a card number, cardholder name, expiry, or security code. A test asserts those names are absent from the payment schema and from the payments table.

**invoices**

| Column | Notes |
| --- | --- |
| id | Primary key |
| invoice_number | Unique integer, assigned in order. A PDF needs a stable identifier. |
| payment_id | Unique foreign key. One invoice per successful purchase. |
| subscription_id | |
| client_id | |
| company_id | |
| company_name_snapshot | |
| client_name_snapshot | |
| client_email_snapshot | |
| package_name_snapshot | |
| package_price_snapshot | |
| duration_snapshot | |
| data_allowance_snapshot | |
| speed_snapshot | |
| amount_paid | |
| currency | |
| pdf_path | Local file path of the generated PDF |
| issued_at | |

The PDF contains the company, the package, and the client, plus the amount paid, the currency, the invoice number, and the issue time. No tax block is added. No card data is printed.

**complaints**

| Column | Notes |
| --- | --- |
| id | Primary key |
| client_id | |
| kind | `complaint` or `technical_support` |
| target | `company` or `platform` |
| company_id | Required when target is `company`. Empty when target is `platform`. |
| message | The text the client submits |
| created_at | |
| reply_message | Nullable. Filled when the company manager replies. |
| replied_by | Nullable foreign key to the manager user |
| replied_at | Nullable |

One reply is stored because the description asks the company manager to reply. A longer thread, attachments, and an admin reply are Open Question 9.

**notifications**

| Column | Notes |
| --- | --- |
| id | Primary key |
| client_id | |
| subscription_id | |
| kind | `expiry_approaching` only |
| message | Arabic text generated from the subscription |
| created_at | |

Unique on (`subscription_id`, `kind`) so each subscription produces one expiry notice. No other notification kinds are stored.

**platform_settings**

| Column | Notes |
| --- | --- |
| key | Primary key |
| value | String |
| updated_at | |
| updated_by | Foreign key to the Platform Admin user |

Rows are inserted only for keys you name in Open Question 11. An empty settings catalog is not invented.

Sales and platform-performance figures are queries over `payments` and `subscriptions`. They do not have their own tables.

### 3.2 Relationships

```mermaid
erDiagram
  users ||--o| company_managers : "is manager"
  companies ||--o| company_managers : "has one manager"
  companies ||--o{ company_join_requests : "may result from"
  companies ||--o{ packages : "offers"
  companies ||--o{ coupons : "issues"
  users ||--o{ subscriptions : "client holds"
  companies ||--o{ subscriptions : "sells"
  packages ||--o{ subscriptions : "is bought as"
  users ||--o{ payments : "pays"
  companies ||--o{ payments : "receives"
  packages ||--o{ payments : "priced from"
  coupons ||--o{ payments : "may discount"
  subscriptions ||--o{ payments : "funded by"
  payments ||--o| invoices : "success produces"
  users ||--o{ complaints : "submits"
  companies ||--o{ complaints : "may be the target"
  users ||--o{ notifications : "receives"
  subscriptions ||--o{ notifications : "warns about"
```

### 3.3 Company status

| Status | Meaning in the product |
| --- | --- |
| `pending` | Join request exists and has not been decided. Required so approve/reject has a prior state. |
| `approved` | The company is available for a client to choose, while it is not suspended or stopped. |
| `rejected` | The admin rejected the join request. Hidden from the client company list. No manager is created from a rejection. |
| `suspended` | The admin applied تعليق. Hidden from the client company list. New purchases are refused. |
| `stopped` | The admin applied إيقاف. Hidden from the client company list. New purchases are refused. |

Whether `suspended` and `stopped` are two different life cycles or two words for one action is Open Question 2. Both values are reserved so the words in the description each have a place. The behavioral difference, the effect on an already-active subscription, and whether the manager can still log in are part of that question. Phase 2 implements the status column and the client-list filter. The part of the admin UI that picks between suspend and stop waits for Open Question 2.

A company appears in the client’s company list only when its status is `approved`.

### 3.4 Subscription day rule

This rule is what “days remaining” and “expired” mean during implementation:

- `days_remaining = max(0, end_date - today)` in whole days, using the timezone from Open Question 8.
- Status is `active` while `today <= end_date`.
- Status is `expired` when `today > end_date`.

The value is corrected on read and by the daily job in Phase 8, so the screen is right even if the job has not run yet. A third stored status is not added unless Open Question 6 says that “stop” is its own status.

---

## 4. Folder structure

Backend and frontend stay in separate folders, as required. `backend` is the Python package. The feature folders follow the required shape: `models.py`, `schemas.py`, `services.py`, `routes.py`, `__init__.py`.

Files beyond that shape are only the ones FastAPI, Alembic, the admin seed, and tests need in order to run. Feature business code does not grow extra modules; the payment interface and the mock provider live in `payments/services.py`.

```text
project-root/
├── PLAN.md
├── backend/
│   ├── __init__.py
│   ├── main.py                  # app factory, router registration, CORS
│   ├── config.py                # environment settings, including DATABASE_URL
│   ├── db.py                    # engine, session, SQLite foreign-key pragma
│   ├── enums.py
│   ├── errors.py
│   ├── middleware.py            # unhandled-error middleware
│   ├── utils.py                 # dates, money rounding
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env.example
│   ├── migrations/
│   │   └── versions/
│   ├── scripts/
│   │   └── seed_admin.py
│   ├── tests/
│   │   ├── conftest.py
│   │   └── <feature>/
│   ├── _core/
│   │   ├── __init__.py
│   │   ├── security.py          # password hash, JWT create/verify
│   │   ├── redis_client.py      # token key read/write/delete only
│   │   ├── deps.py              # current user, role guards, company scope
│   │   ├── permissions.py
│   │   └── email.py             # Arabic purchase-confirmation mail
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── routes.py
│   ├── companies/
│   ├── packages/
│   ├── coupons/
│   ├── payments/
│   ├── subscriptions/
│   ├── invoices/
│   ├── notifications/
│   ├── complaints/
│   ├── reports/
│   └── settings/
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── .env.example
    └── src/
        ├── app/
        │   ├── layout.tsx                 # lang="ar" dir="rtl", theme class
        │   ├── globals.css
        │   ├── page.tsx                   # sends the visitor to login
        │   ├── (public)/
        │   │   ├── login/page.tsx
        │   │   └── register/page.tsx
        │   ├── (client)/
        │   │   └── client/...
        │   ├── (company)/
        │   │   └── company/...
        │   └── (admin)/
        │       └── admin/...
        ├── components/
        │   ├── ui/                        # button, field, table/card, modal
        │   └── shell/                     # header, nav, theme toggle
        ├── features/
        │   ├── auth/
        │   ├── companies/
        │   ├── packages/
        │   ├── coupons/
        │   ├── payments/
        │   ├── subscriptions/
        │   ├── invoices/
        │   ├── notifications/
        │   ├── complaints/
        │   ├── reports/
        │   └── settings/
        ├── lib/
        │   ├── api.ts
        │   └── auth-storage.ts
        └── messages/
            └── ar.ts                      # every user-visible string
```

Each `features/<name>/` folder on the frontend holds that feature’s API calls and screens. Shared visual pieces stay in `components/`. Role layouts stay in the route groups `(public)`, `(client)`, `(company)`, and `(admin)`.

`tests/` is included so each phase has an automated check for permissions and tenant isolation. It is not a product feature.

### Backend file roles

| File | Role |
| --- | --- |
| `models.py` | SQLAlchemy tables for that feature |
| `schemas.py` | Pydantic request and response bodies |
| `services.py` | Business rules and queries |
| `routes.py` | HTTP only: read the body, call the service, return the schema |
| `_core/deps.py` | Authentication and the role/company guards used by routes |
| `middleware.py` | Turns unexpected exceptions into the standard error body |
| `errors.py` | `AppError` with an HTTP status, a stable `code`, and an Arabic `message` |

Routes do not query the database. Services do not read raw `Request` objects.

### Frontend routes

English path segments, Arabic screen text.

| Path | Who | Purpose |
| --- | --- | --- |
| `/login` | All | Login |
| `/register` | Visitor | Client registration |
| `/client/companies` | Client | Choose a company |
| `/client/companies/[companyId]/packages` | Client | That company’s packages |
| `/client/checkout/[packageId]` | Client | Buy, coupon, mock payment outcome |
| `/client/subscriptions` | Client | History across companies, status, days remaining |
| `/client/subscriptions/[id]` | Client | One subscription, renew, invoice download |
| `/client/notifications` | Client | Expiry notices |
| `/client/complaints` | Client | Submit a complaint or a support request, and the list of what this client submitted |
| `/company` | Company Manager | Own-company home linking only to that company’s tools |
| `/company/packages` | Company Manager | List, create, edit, delete |
| `/company/coupons` | Company Manager | List and create |
| `/company/clients` | Company Manager | Clients of this company and their subscriptions |
| `/company/subscriptions/[id]` | Company Manager | One subscription: follow it, and the activate / renew / review / stop actions once their rules are confirmed |
| `/company/reports` | Company Manager | Sales and profits for this company |
| `/company/complaints` | Company Manager | Complaints for this company, and the reply |
| `/admin/companies` | Platform Admin | Companies, create company + manager, suspend/stop |
| `/admin/join-requests` | Platform Admin | Approve or reject |
| `/admin/performance` | Platform Admin | Platform-wide totals |
| `/admin/complaints` | Platform Admin | Complaints targeted at the platform |
| `/admin/settings` | Platform Admin | General settings |

---

## 5. Phases

Shared rules for every phase:

- User-visible text comes from `frontend/src/messages/ar.ts`.
- Each phase’s screens are checked at 360, 768, 1024, and 1440 pixels, in light and in dark.
- A Company Manager request is scoped with the `company_id` inside the token. The service ignores any company id in the body or query for those routes.
- Automated tests for the phase use SQLite and a Redis stand-in that speaks the same token commands. The manual checklist uses a real Redis.
- API errors use `{ "code": "...", "message": "..." }` with the message in Arabic.
- At the stop, report what was completed, the commands to run, and the checklist. Wait for confirmation.

A part marked **Blocked** is specified here and is coded only after the listed open question is answered. Unblocked parts of the same phase can be built and then the phase stops on the blocked part.

### Phase 0 — Foundation

**Goal.** A running API and an Arabic website shell. The Platform Admin can log in and log out. Tokens die on logout. Role guards exist. No business feature yet.

**Blocked.** Nothing in this phase.

#### Backend

- Create the tree in section 4, with empty feature packages that export no routes yet.
- `config.py` loads the environment variables in section 6. Default `DATABASE_URL` is SQLite (`sqlite:///./backend/dev.db`).
- `db.py` creates the engine from `DATABASE_URL` and enables SQLite foreign keys.
- Alembic is initialized. The first migration creates `users` only. Later phases add their own migrations.
- Redis client exposes three operations: store a token id with a TTL, check that it exists, delete it. No other Redis commands are wrapped, so later work has nowhere to “borrow” Redis.
- Password hashing with bcrypt.
- JWT access token claims: `sub` (user id), `role`, `company_id` (null except for a company manager), `jti`, `exp`.
- Login stores `auth:token:{jti}` in Redis with TTL `ACCESS_TOKEN_TTL_SECONDS` and returns the token.
- Logout deletes that key.
- Every protected route verifies the signature and the expiry, then requires the Redis key. A missing key is an expired session even if the JWT signature is still valid.
- Guards in `_core/deps.py`: `require_client`, `require_company_manager`, `require_platform_admin`.
- `scripts/seed_admin.py` creates one `platform_admin` user from `PLATFORM_ADMIN_EMAIL` and `PLATFORM_ADMIN_PASSWORD` when that email is absent. Running it twice does not create a second admin or change the password.
- `GET /api/health` reports whether the database session and Redis respond. This is an operations check for this phase.

#### Frontend

- Next.js App Router project, TypeScript, Tailwind, `lang="ar"` and `dir="rtl"` on `<html>`.
- Noto Sans Arabic.
- Theme class `light` or `dark` on `<html>`. First visit uses light. The header control switches the theme and stores the choice in `localStorage` under `theme`.
- Public layout with the theme control, login page, and empty role layouts that redirect to `/login` when there is no token.
- Login form calls the API. The token is kept in `sessionStorage`. Logout calls the API and clears the stored token.
- After login, send each role to its home: admin to `/admin/companies`, company manager to `/company`, client to `/client/companies`. Those homes may be empty shells until their phases.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/health` | Public |
| `POST` | `/api/auth/login` | Public |
| `POST` | `/api/auth/logout` | Any logged-in user |
| `GET` | `/api/auth/me` | Any logged-in user |

`POST /api/auth/login` body: `email`, `password`. Response: `access_token`, `role`, `full_name`.

#### Verification

- Seed the admin, log in, call `/api/auth/me`, log out, call `/api/auth/me` again and get 401.
- Log in, delete the Redis key by logging out, confirm the old token is rejected.
- Call an admin-only test route with a non-admin token and get 403. (A temporary route in the test suite is enough; it is not registered in the real app.)
- Open the login page at 360, 768, 1024, and 1440. Confirm Arabic text, RTL alignment, and both themes.
- Confirm the theme survives a refresh.

#### Done when

- Backend tests for login, logout, and the role guard pass.
- You have received the admin email and password from the environment used for the seed.
- The checklist above has been run.

#### Stop

Stop. Report the commands, the admin credentials, and how you ran the checklist. Wait for confirmation before Phase 1.

While waiting, the open questions in section 11 can be answered in any order. A later phase that is blocked stays blocked until its question is answered.

---

### Phase 1 — Client registration

**Goal.** A visitor can create a client account and then log in with it. Registration cannot create an admin or a company manager.

**Blocked.** The field list and the password rule are Open Question 12. The phase starts after that answer. The rest of the phase is fixed.

#### Backend

- `POST /api/auth/register` accepts only the fields from Open Question 12, plus email and password.
- Role is always `client`. Any submitted role is ignored.
- Duplicate email returns 409 with an Arabic message.
- Password rule is exactly the rule from Open Question 12.
- The endpoint returns the same login payload as `POST /api/auth/login` and stores a Redis token, so the new client is logged in.

#### Frontend

- `/register` in Arabic, link from `/login` and back.
- Same shell, theme, and breakpoints as Phase 0.
- Success lands on `/client/companies` (the page itself arrives in Phase 2; until then the client layout’s empty home is acceptable only inside this phase’s demo, and Phase 2 replaces it).

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Public |

#### Verification

- Register a client, receive a token, `/api/auth/me` shows `client`.
- Register the same email again and get 409.
- Submit `role: platform_admin` and confirm the stored role is `client`.
- A password that breaks the confirmed rule is rejected.
- Layout check at the four widths and both themes.

#### Done when

- The cases above pass against the field list you confirmed.

#### Stop

Stop. Report how to register a client and how you verified the role cannot be escalated. Wait for confirmation before Phase 2.

---

### Phase 2 — Companies and company managers

**Goal.** The Platform Admin can create one company and its single manager. The client can open a list of available companies and choose one. Suspended, stopped, pending, and rejected companies stay off that list.

**Blocked.**

- Join-request intake, and therefore clicking Approve/Reject on real submitted rows: Open Question 1.
- The behavioral difference between suspend and stop, existing subscriptions, and manager login during a suspension: Open Question 2. The status values exist; the admin control that chooses between them waits.

#### Backend

- Migration for `companies`, `company_managers`, and `company_join_requests` (request payload columns only after Open Question 1).
- Platform Admin creates a company with status `approved` and, in the same action, the manager user (`full_name`, `email`, `password`) linked in `company_managers`. This is the specified in-platform creation path.
- The manager’s JWT `company_id` is that company.
- A second manager for the same company is rejected. A second company for the same manager is rejected.
- `GET /api/companies` for a client returns only `approved` companies: `id` and `name`.
- `POST /api/admin/companies/{id}/suspend` and `POST /api/admin/companies/{id}/stop` set the matching status once Open Question 2 is answered. Until then the routes are not exposed.
- Join-request routes, once Open Question 1 is answered:
  - `GET /api/admin/join-requests`
  - `POST /api/admin/join-requests/{id}/approve`
  - `POST /api/admin/join-requests/{id}/reject`
- Approve links or creates the company as `approved` and does not by itself invent a manager. The admin then uses the create-manager action. If your answer to Open Question 1 says approval must create the manager in one step, the approve service will do that and the separate create action will only be used when you still want it.
- Reject sets the request to `rejected` and does not create a manager.

#### Frontend

- Admin: `/admin/companies` lists companies and their statuses. A form creates the company name and the manager’s name, email, and password. The password is shown to the admin once so you can hand it to the manager. The system does not email the manager, because that email is not in the description.
- Admin: `/admin/join-requests` lists pending requests and has Approve and Reject. The page is built with the routes and stays empty of a submission form until Open Question 1 is answered.
- Client: `/client/companies` shows the available companies. Choosing one stores `selectedCompanyId` in the client UI and opens that company’s package list (the list arrives in Phase 3; this phase navigates to the route).
- Company: `/company` is the manager shell with navigation only to this company’s later pages. The home itself shows the company name and no other company’s data.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/companies` | Client |
| `POST` | `/api/admin/companies` | Platform Admin. Body: company `name`, manager `full_name`, `email`, `password`. |
| `GET` | `/api/admin/companies` | Platform Admin |
| `GET` | `/api/admin/join-requests` | Platform Admin. Blocked on Open Question 1. |
| `POST` | `/api/admin/join-requests/{id}/approve` | Platform Admin. Blocked on Open Question 1. |
| `POST` | `/api/admin/join-requests/{id}/reject` | Platform Admin. Blocked on Open Question 1. |
| `POST` | `/api/admin/companies/{id}/suspend` | Platform Admin. Blocked on Open Question 2. |
| `POST` | `/api/admin/companies/{id}/stop` | Platform Admin. Blocked on Open Question 2. |
| `GET` | `/api/company/me` | Company Manager. Returns that manager’s company only. |

#### Verification

- Admin creates Company A and Manager A, and Company B and Manager B.
- Manager A logs in and `GET /api/company/me` returns Company A.
- Manager A calling `/api/admin/companies` receives 403.
- Client company list shows A and B after they are approved, and hides a company whose status is not `approved`.
- Creating a second manager for Company A fails.
- Four widths, both themes, Arabic labels: الشركات، لوحة الشركة.

#### Done when

- Two companies are isolated in the API tests.
- You can log in as a manager you created.
- Join-request approve/reject is included in this “done” only after Open Question 1 is implemented and checked.
- Suspend and stop are included in this “done” only after Open Question 2 is implemented and checked.

#### Stop

Stop. If an open question for this phase is still unanswered, say so and stop before that part. Otherwise report how to create a manager and how you confirmed Company A cannot see Company B. Wait for confirmation before Phase 3.

---

### Phase 3 — Packages

**Goal.** A company manager can add, edit, and delete that company’s packages. A client who has selected a company sees that company’s packages with name, price, duration, data allowance, and speed.

**Blocked.** Open Question 3 (units, and what delete does when a subscription already points at the package). The phase starts after that answer, because the package form and the end-date math depend on it.

#### Backend

- Migration for `packages` using the column shapes from Open Question 3.
- Create, update, and delete are limited to the manager’s `company_id`.
- A client `GET /api/companies/{companyId}/packages` returns packages only when that company is `approved`.
- Delete follows the rule you give in Open Question 3.

#### Frontend

- `/company/packages`: list, create, edit, delete, Arabic labels for المدة والحجم والسرعة والسعر.
- `/client/companies/[companyId]/packages`: cards or a stacked list on narrow screens, a roomier grid from 1024 up. Each package shows name, price, duration, data allowance, and speed.
- A package page for Company B is unreachable from Manager A’s UI. Direct API calls are covered in the tests.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/company/packages` | Company Manager |
| `POST` | `/api/company/packages` | Company Manager |
| `PATCH` | `/api/company/packages/{id}` | Company Manager |
| `DELETE` | `/api/company/packages/{id}` | Company Manager |
| `GET` | `/api/companies/{companyId}/packages` | Client |

#### Verification

- Manager A creates a package and sees it. Manager B does not.
- Manager A updating Manager B’s package id receives 404.
- Client sees the package under Company A and does not see it under Company B.
- A non-approved company returns an empty result, or 404 if the company itself is not available. Use 404 when the company is not available so the client list and the package list agree.
- Four widths, both themes. Long Arabic package names wrap and do not overflow the screen.

#### Done when

- CRUD and the client read path pass the tests, including the delete rule you confirmed.

#### Stop

Stop. Report how to create a package as the manager and see it as the client. Wait for confirmation before Phase 4.

---

### Phase 4 — Coupons

**Goal.** A company manager can create discount coupons for that company only, and can see the coupons already created. Clients do not get a coupon-management screen. Entering a code happens at checkout in Phase 6.

**Blocked.** Open Question 4 (discount type, value, expiry, usage limits, and whether a renewal may use a coupon). The phase starts after that answer.

The description asks the manager to create coupons. It does not ask for edit or delete, so there is no update or delete endpoint.

#### Backend

- Migration adds the coupon columns required by your answer.
- Create rejects a duplicate code within the same company.
- The same code may be created by another company.
- List returns only the caller’s company.

#### Frontend

- `/company/coupons` with a create form and a list of this company’s codes.
- Navigation item: الكوبونات.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/company/coupons` | Company Manager |
| `POST` | `/api/company/coupons` | Company Manager |

#### Verification

- Manager A creates code `SAVE`. Manager B can also create `SAVE`. Manager A’s list does not show Manager B’s row.
- A client token receives 403 on these routes.
- Four widths, both themes.

#### Done when

- The create and list tests pass, including same-code-different-company.

#### Stop

Stop. Report how to create a coupon and how you checked the other company cannot see it. Wait for confirmation before Phase 5.

---

### Phase 5 — Payment layer and mock provider

**Goal.** A replaceable payment interface and a mock provider that can succeed and fail. No card data is accepted or stored. Subscriptions are not created in this phase; Phase 6 is the first caller.

**Blocked.** Open Question 7 (currency code). The interface takes a currency string from configuration. The phase starts after the code is set in the environment.

#### Backend

Implement the design in section 7 inside `payments/services.py`, plus the `payments` table migration.

- `get_payment_provider()` returns `MockPaymentProvider` when `PAYMENT_PROVIDER=mock`.
- Public payment routes do not exist in this phase. The mock is called by the purchase service in Phase 6.
- Schemas used by checkout reject unknown card fields (`card_number`, `pan`, `cvv`, `cvc`, `expiry`).

#### Frontend

No payment page in this phase. The mock’s success and failure controls are part of the checkout screen in Phase 6, because that is where a purchase happens.

#### API

None exposed yet. The service function is covered by tests:

- `charge` with `simulated_outcome=success` returns `succeeded` and a reference.
- `charge` with `simulated_outcome=failure` returns `failed` and `failure_code=mock_declined`.
- A schema fixture that includes `card_number` is rejected.

#### Verification

- The three tests above.
- Inspect the `payments` model and confirm there is no card column.

#### Done when

- Those tests pass and `PAYMENT_PROVIDER` is the only switch for the implementation.

#### Stop

Stop. Report the test command and that no card field exists. Wait for confirmation before Phase 6.

---

### Phase 6 — Subscriptions, purchase, and renewal

**Goal.** A logged-in client can buy a package from the selected company. A successful mock payment creates an active subscription. A failed mock payment creates neither a subscription nor an invoice nor an email. The client can see status, days remaining, and history across companies. The manager can see that company’s clients and their subscriptions.

**Blocked.**

- Renewal behavior, and more than one active subscription for the same client at the same company: Open Question 5.
- Manager activate, review, and stop: Open Question 6.
- Coupon math at checkout: Open Question 4, already required for Phase 4. Checkout applies a coupon only under those rules. If a coupon is not allowed on renewal, the renew form has no coupon field.

Purchase of a **new** subscription is not blocked: success creates a row with status `active`, `start_date` today, and `end_date` from the package duration.

#### Backend

- Migration for `subscriptions`.
- `POST /api/subscriptions/purchases` runs the sequence in section 7.4.
- Idempotency: the same `idempotency_key` returns the original result and does not create a second subscription.
- Failed payment: a `payments` row with `failed`, no subscription row.
- `GET /api/subscriptions` for the client returns every subscription that client has, with company name, package snapshot, status, start, end, and `days_remaining`.
- `GET /api/company/clients` returns distinct clients who have at least one subscription with the manager’s company, and each client’s subscriptions for that company only.
- `GET /api/company/subscriptions/{id}` returns one subscription when it belongs to the manager’s company. This is the “follow / review the record” screen. A separate review workflow is added only if Open Question 6 defines one.
- Renew, activate, and stop routes are added from the answers to Open Questions 5 and 6. They call the same services the client renewal uses where both roles are allowed to renew.

#### Frontend

- Checkout page: selected company, package summary, optional coupon code, and two mock actions, نجاح الدفع and فشل الدفع. Those two actions are sent as `simulated_outcome` and are rendered only when the API reports the active provider is `mock`.
- Success screen shows status `نشط` and days remaining. Invoice download and the “email sent” line are added in Phase 7; this phase’s success screen states that the subscription is active.
- `/client/subscriptions` lists every company, with status and days remaining. Narrow screens use one card per subscription.
- `/company/clients` lists this company’s clients and their subscriptions.
- Subscription detail for the manager includes the activate, renew, and stop controls once their questions are answered.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `POST` | `/api/subscriptions/purchases` | Client. Body: `company_id`, `package_id`, optional `coupon_code`, `idempotency_key`, and `simulated_outcome` only while the provider is `mock`. |
| `GET` | `/api/subscriptions` | Client |
| `GET` | `/api/subscriptions/{id}` | Client, own row only |
| `POST` | `/api/subscriptions/{id}/renew` | Client. Blocked on Open Question 5. |
| `GET` | `/api/company/clients` | Company Manager |
| `GET` | `/api/company/subscriptions/{id}` | Company Manager |
| `POST` | `/api/company/subscriptions/{id}/renew` | Company Manager. Blocked on Open Question 5. |
| `POST` | `/api/company/subscriptions/{id}/activate` | Company Manager. Blocked on Open Question 6. |
| `POST` | `/api/company/subscriptions/{id}/stop` | Company Manager. Blocked on Open Question 6. |

#### Verification

- Client buys from Company A with mock success. The subscription is `active`, the end date matches the duration rule, and days remaining matches section 3.4.
- The same purchase with mock failure leaves no subscription.
- Repeating the same idempotency key does not create a second subscription.
- A coupon for Company B is rejected on a Company A purchase.
- Client history shows subscriptions from Company A and Company B together.
- Manager A sees the client. Manager B does not, including by guessing the subscription id (404).
- A package that belongs to Company B cannot be bought with Company A’s id.
- Four widths, both themes. The two mock buttons are usable at 360px.

#### Done when

- The unblocked checks pass.
- Renewal and the manager state changes are part of “done” only after their open questions are implemented and checked.

#### Stop

Stop. Report the success path and the failure path. If renewal or manager actions are still blocked, stop before them and ask for those answers. Wait for confirmation before Phase 7.

---

### Phase 7 — PDF invoices and confirmation email

**Goal.** Every successful purchase produces one PDF invoice and one Arabic confirmation email to the client’s account email. The email is sent only after success. Failure of the mock payment sends nothing and creates no invoice.

**Blocked.** Open Question 13 (what happens if the PDF or the email fails after the payment has already succeeded). The happy path is specified and can be built; the failure policy inside this phase waits for that answer before the phase is called done.

#### Backend

- Migration for `invoices`.
- On payment success, after the subscription is stored: render the PDF, store the file under `INVOICE_STORAGE_DIR`, insert the invoice row, send the email with the PDF attached.
- Email body in Arabic: company name, package name, period, amount paid, invoice number. No card data.
- `GET /api/invoices/{id}/pdf` returns the file only to the client who owns it, or to the manager of that invoice’s company. The Platform Admin does not download company invoices; invoice files are company data.
- Development `EMAIL_BACKEND=console` prints the message and writes the PDF bytes path to the log. `EMAIL_BACKEND=smtp` sends with the SMTP settings. The call site does not change between them.

#### Frontend

- On the purchase success screen: a download action فاتورة PDF, and a line that the confirmation email was sent.
- The subscription detail page includes the same download for each successful purchase tied to that subscription.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/subscriptions/{id}/invoices` | Client, own subscription |
| `GET` | `/api/invoices/{id}/pdf` | Owning client, or that company’s manager |

#### Verification

- Successful purchase: one invoice row, a PDF that opens and contains the company name, package name, client name, and client email, and a console email containing the same facts and the attachment.
- Failed purchase: no invoice row and no email log line.
- Manager B cannot download Company A’s invoice (404).
- A second purchase produces a second invoice and a second email.
- Four widths, both themes. The download control is visible on a phone-width success screen.

#### Done when

- The happy path above passes, and the failure policy from Open Question 13 is implemented and checked.

#### Stop

Stop. Report where to read the console email and where to open the PDF. Wait for confirmation before Phase 8.

---

### Phase 8 — Expiry notifications

**Goal.** A client receives one notification when a subscription is close to ending, and can read it in the website.

**Blocked.** Open Question 8 (how many days before the end, the timezone, and whether email is added beside the in-app notice). The phase starts after that answer.

The description names this as an إشعار, and it names email separately for purchases. The in-app notice is the required channel. A second channel is added only if your answer includes it.

#### Backend

- Migration for `notifications`.
- A daily job inside the API process (APScheduler). It does not use Redis. Redis stays limited to tokens.
- The job loads active subscriptions whose end date is within the confirmed window, inserts one `expiry_approaching` row if that pair does not exist, and flips status to `expired` when `today > end_date`.
- `GET /api/notifications` returns the caller’s notices only.

#### Frontend

- `/client/notifications` lists the Arabic messages, newest first.
- Navigation item: الإشعارات.
- Empty state in Arabic when there are none.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/notifications` | Client |
| `POST` | `/api/notifications/run-expiry-check` | Platform Admin, so the checklist can run the job without waiting a day |

The run endpoint exists so the phase can be tested. It performs the same job as the daily scheduler.

#### Verification

- Create a subscription whose end date falls inside the window. Run the check. The client sees one Arabic notice. Running the check again does not create a second notice.
- A subscription outside the window produces no notice.
- Manager and admin tokens do not see the client’s notice list (403).
- Four widths, both themes.

#### Done when

- One notice per subscription per window, for the threshold and timezone you confirmed.

#### Stop

Stop. Report the date you used and the notice text. Wait for confirmation before Phase 9.

---

### Phase 9 — Complaints and technical support

**Goal.** A client can submit either a complaint or a technical-support request. The target is either a company the client deals with, or the platform. The company manager replies to items targeted at that company. The Platform Admin follows items targeted at the platform.

**Blocked.** Open Question 9 (which companies count as “a company the client deals with”, whether the client sees the reply, and whether the admin replies or only follows). The phase starts after that answer.

#### Backend

- Migration for `complaints`.
- Create validates `kind` and `target`. A company target requires `company_id` and the relationship rule from Open Question 9.
- Manager list and reply are filtered by token `company_id`. Reply fills `reply_message`, `replied_by`, and `replied_at`.
- Admin list returns only `target=platform`.
- If your answer says the client can read replies, `GET /api/complaints` includes the reply fields for the owner. If your answer says the admin replies, a platform-reply path is added then and is absent until then.

#### Frontend

- Client form: kind (شكوى / طلب دعم فني), target (شركة / المنصة), company selector limited by the confirmed rule, message.
- Manager: list and a reply box on each company complaint.
- Admin: list of platform complaints, with a reply box only if Open Question 9 adds replies.
- Navigation: الشكاوى والدعم for the client, الشكاوى for the manager, الشكاوى العامة for the admin.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `POST` | `/api/complaints` | Client |
| `GET` | `/api/complaints` | Client, own rows. Reply fields depend on Open Question 9. |
| `GET` | `/api/company/complaints` | Company Manager |
| `POST` | `/api/company/complaints/{id}/reply` | Company Manager |
| `GET` | `/api/admin/complaints` | Platform Admin, platform target only |

#### Verification

- Client submits one company complaint and one platform support request.
- Manager A sees and replies to the company item. Manager B receives 404 on that id.
- The platform item appears on the admin list and does not appear on a manager list.
- A client cannot target a company forbidden by the rule you confirmed.
- Four widths, both themes. The form is usable at 360px.

#### Done when

- The routing above matches your answer to Open Question 9, including reply visibility.

#### Stop

Stop. Report the two submissions and which role could see each. Wait for confirmation before Phase 10.

---

### Phase 10 — Company sales and profits

**Goal.** The company manager can follow sales and profits for that company only.

**Blocked.** Open Question 10 (how profit differs from sales). Sales themselves are defined below and can be built with the profit section present only after the answer. The phase is done when both numbers you confirmed are on the screen.

#### Sales definition

Sales are the successful payments for this company: a list (date, client name, package name, amount) and the total of those amounts. Failed payments are excluded. Other companies’ payments are excluded.

Profit is displayed with the formula from Open Question 10 and is not given a stand-in formula.

#### Backend

- `GET /api/company/reports/sales` aggregates from `payments` where `status=succeeded` and `company_id` is the token company.
- Profit is a field on that response only after Open Question 10.

#### Frontend

- `/company/reports` title المبيعات والأرباح.
- Totals and the sales list. The list becomes cards under 768px.
- No control that selects another company.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/company/reports/sales` | Company Manager |

#### Verification

- Two successful purchases at Company A and one at Company B. Manager A’s total equals only A’s two amounts.
- A failed payment is absent from the total.
- A client token receives 403.
- Four widths, both themes.

#### Done when

- Sales match the definition above and profit matches your formula.

#### Stop

Stop. Report the figures you compared. Wait for confirmation before Phase 11.

---

### Phase 11 — Platform performance

**Goal.** The Platform Admin can monitor performance of the platform as the aggregate of all companies, without opening a company’s private management screens.

**Blocked.** Open Question 10 also covers which totals belong on this screen. The phase starts after that list is confirmed. The admin does not gain package, coupon, or client-management tools in this phase.

#### Backend

- `GET /api/admin/performance` returns only the aggregates you name. Each aggregate is computed across companies. The response does not include per-client message text, coupon codes, or invoice PDFs.

#### Frontend

- `/admin/performance` title أداء المنصة.
- One area per confirmed metric. Figures that are sums are labeled as totals across companies.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/admin/performance` | Platform Admin |

#### Verification

- The numbers match a hand count of the confirmed metrics across Company A and Company B.
- A company manager receives 403.
- The page has no link that edits another company’s packages or coupons.
- Four widths, both themes.

#### Done when

- The confirmed metrics match the database, and company-private pages stay unavailable to the admin.

#### Stop

Stop. Report the metrics and the hand count. Wait for confirmation before Phase 12.

---

### Phase 12 — Platform settings

**Goal.** The Platform Admin can manage the general settings of the application.

**Blocked.** Open Question 11 (the key, the meaning, the default, and who can read each setting). The phase starts after you list the keys. No placeholder settings are inserted.

#### Backend

- Migration for `platform_settings`.
- Seed the defaults you provide, as rows, in the Phase 12 migration or a small settings seed run by the admin command. This seed is for setting defaults, not for a second admin user.
- `GET` and `PUT /api/admin/settings` read and update only those keys.
- If a setting must affect client or manager screens, the read endpoint for that key is limited to the roles you name in the answer.

#### Frontend

- `/admin/settings` with one Arabic-labeled control per key.

#### API

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/api/admin/settings` | Platform Admin |
| `PUT` | `/api/admin/settings` | Platform Admin |

#### Verification

- Change a setting, refresh, and see the stored value.
- A manager and a client receive 403 on the admin settings route.
- Any client-readable setting you confirmed is visible in the place you named, and nowhere else.
- Four widths, both themes.

#### Done when

- Every key you listed can be read and updated by the Platform Admin, and only there, unless you explicitly marked a key as readable by another role.

#### Stop

Stop. Report the settings you changed. This is the last phase. After your confirmation, the system described in this plan is complete.

---

## 6. Technical decisions

### 6.1 Frontend library

**Next.js (App Router) with React, TypeScript, and Tailwind CSS.**

The API is already a separate FastAPI service, so the website’s job is pages, layouts, and Arabic presentation. App Router layouts map onto the four shells this product needs: public, client, company manager, and platform admin. Shared RTL, theme, and navigation live in those layouts. Next.js route handlers are not used for business data.

React with Vite would be a sound SPA in front of FastAPI. Next.js is the better fit here because the product is a multi-role website with a persistent shell per role, not a single screen.

Vue and Nuxt could build the same UI. This plan uses React and Next.js because role-based layouts plus Tailwind’s logical spacing utilities are a direct way to keep one Arabic, theme-aware website in front of FastAPI.

Tailwind is the styling layer because the layout requirements are concrete: RTL logical spacing (`ms`, `me`, `ps`, `pe`, `text-start`, `text-end`), a `dark` class, and width breakpoints. A component kit that assumes left-to-right pages is not used. Small local components (button, field, modal, table/card) live in `components/ui`.

There is no second language catalog. Strings live in `messages/ar.ts`.

### 6.2 Authentication and Redis

- One JWT access token per login. No refresh token. Logout is real because the server forgets the token id.
- Claims: `sub`, `role`, `company_id`, `jti`, `exp`. Signed with `JWT_SECRET` (HS256).
- Redis key `auth:token:{jti}` stores the user id, with TTL `ACCESS_TOKEN_TTL_SECONDS` (default 86400). Login writes the key. Logout deletes it. Protected routes require the key.
- Redis is not used for cache, queues, rate limits, or job locks. The expiry job uses APScheduler in the API process and the database.
- The frontend sends `Authorization: Bearer` and keeps the token in `sessionStorage` so a new browser session must log in again. The frontend and API are separate origins during development, which keeps the CORS setup explicit.
- CORS allows only `CORS_ORIGINS`.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLite in development, PostgreSQL in production |
| `REDIS_URL` | Token store |
| `JWT_SECRET` | Token signature |
| `ACCESS_TOKEN_TTL_SECONDS` | Session length |
| `PLATFORM_ADMIN_EMAIL` | Seeded admin |
| `PLATFORM_ADMIN_PASSWORD` | Seeded admin |
| `CORS_ORIGINS` | Frontend origin |
| `PAYMENT_PROVIDER` | `mock` until a real provider is chosen |
| `PAYMENT_CURRENCY` | Set from Open Question 7 |
| `EMAIL_BACKEND` | `console` or `smtp` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM` | Used when the backend is `smtp` |
| `INVOICE_STORAGE_DIR` | PDF files |
| `NEXT_PUBLIC_API_URL` | Frontend API base |

`.env` files are not committed. `.env.example` lists the keys with empty secrets.

### 6.3 PDF generation

**fpdf2**, with **arabic-reshaper** and **python-bidi**, and a bundled Noto Naskh Arabic font file.

Reason: the deployment machine in development is Windows, and fpdf2 does not need the native libraries WeasyPrint requires. Arabic shaping libraries are required because plain PDF text does not join Arabic letters. The font file is an open font shipped in `backend/_core/fonts/` so invoice generation does not call a network font service.

The PDF is written to `INVOICE_STORAGE_DIR` and downloaded through the authenticated invoice route.

### 6.4 Email

**The standard-library SMTP client**, behind `backend/_core/email.py`.

- `console` backend: log the Arabic subject and body, and the attachment path. This is what the Phase 7 checklist uses.
- `smtp` backend: send the same message through the SMTP environment variables.

One function, `send_purchase_confirmation(to, subject, body, pdf_path)`, is the only mail the system sends unless Open Question 8 adds an expiry email. No manager-invitation mail is added.

### 6.5 Expiry notification

- Channel: an in-app row in `notifications`, listed at `/client/notifications`.
- Schedule: APScheduler, once a day, inside the API process.
- Deduping: unique (`subscription_id`, `expiry_approaching`).
- Threshold, timezone, and any extra channel: Open Question 8.
- Redis is not involved.

### 6.6 Migrations

**Alembic**, configured with the same `DATABASE_URL` as the app.

Each phase that adds tables ships one migration. Migrations use portable types only: integer, string, numeric, boolean, date, timezone-aware datetime. No `JSONB`, no arrays, no PostgreSQL enums.

### 6.7 Testing

- **pytest** and FastAPI’s test client for each phase: permissions, tenant isolation, and the payment mock.
- Tests run on SQLite with foreign keys on, and on a Redis stand-in limited to the token commands. This keeps the test process free of a second product database while still executing the real service code.
- The manual checklist in each phase is required as well: real Redis, Arabic UI, four widths, both themes.
- A browser pass of the phase’s screens is part of finishing that phase, because the UI is the product surface.

### 6.8 Other implementation rules

- Pagination on list endpoints: 20 rows per page, `page` query parameter, so a long client or payment list still loads. This is a delivery rule for the lists the description already requires.
- Cross-tenant object access returns **404**, so one company cannot learn whether another company’s id exists.
- Wrong role returns **403**. Missing or revoked token returns **401**.
- Duplicate email and a second manager for one company return **409**.
- Package edits do not change snapshots already stored on subscriptions and invoices.
- Purchase idempotency key is required on checkout.

---

## 7. Payment layer and mock provider

The platform never receives or stores card data. The provider is not chosen yet. Business code depends on an interface. The mock is the only implementation in this plan.

### 7.1 Interface

Lives in `backend/payments/services.py`.

```text
PaymentRequest
  amount            Numeric
  currency          string from PAYMENT_CURRENCY
  idempotency_key   string
  client_id         int
  company_id        int
  description       string
  simulated_outcome "success" or "failure"   read only by the mock

PaymentResult
  status                 "succeeded" or "failed"
  provider_reference     string
  failure_code           string or empty

PaymentProvider
  name: string
  charge(request) -> PaymentResult

get_payment_provider(settings) -> PaymentProvider
```

`PaymentRequest` has no card fields. `get_payment_provider` selects the class from `PAYMENT_PROVIDER`. Adding a future provider means a new class and a new branch in that function. Purchase, invoice, and email code keep calling `charge`.

While `PAYMENT_PROVIDER=mock`, checkout accepts `simulated_outcome`. When any other provider name is configured, a request that still sends `simulated_outcome` is rejected, so the test switch cannot force a successful payment in production.

### 7.2 Mock provider

`MockPaymentProvider.charge`:

- `simulated_outcome=success` → `succeeded` plus a generated `provider_reference` (`mock_` + a unique id).
- `simulated_outcome=failure` → `failed`, `failure_code=mock_declined`, plus a reference.
- Any other outcome → error, no charge result.

The mock does not sleep, does not call the network, and does not read card fields.

### 7.3 What is stored

A `payments` row stores amount, currency, provider name, status, provider reference, failure code, and the idempotency key. That is enough to show success and failure and to attach an invoice to a success. Card data is not accepted on the way in and has nowhere to be stored.

### 7.4 Purchase sequence

Used by `POST /api/subscriptions/purchases` and, once renewal is defined, by the renew endpoints.

1. Load the client from the token.
2. Load the company and require status `approved`.
3. Load the package and require `package.company_id == company.id`.
4. If a coupon code was sent, load it for that same company and apply Open Question 4. A code from another company fails the purchase.
5. Compute the amount.
6. Insert a payment row.
7. Call `get_payment_provider().charge(...)`.
8. On failure: mark the payment `failed`, commit, return an Arabic error. Do not create a subscription, invoice, or email.
9. On success: mark the payment `succeeded`, create the subscription as `active` with snapshots and dates, commit.
10. Phase 7 continues the success path: PDF, invoice row, confirmation email.

Renewal steps 9 and 10 follow Open Question 5 (same row extended, or a new row). The payment interface call stays the same.

---

## 8. Screen sizes and Arabic RTL

The UI is Arabic only.

- `<html lang="ar" dir="rtl">` is set in the root layout and is not switched per page.
- Tailwind utilities that encode a physical side (`ml`, `mr`, `pl`, `pr`, `left`, `right`, `text-left`, `text-right`) are not used. Spacing and alignment use `ms`, `me`, `ps`, `pe`, `text-start`, and `text-end`, which follow the RTL direction.
- The sidebar is on the inline-start edge, which is the right edge in RTL, from 1024px upward. Below 1024px it becomes a button-opened drawer.
- Reading pages use a centered container (`max-w-5xl`). Dashboards use the full width with the sidebar.
- Tables are tables from 768px up and one card per row below 768px.
- Primary actions are at least 44px tall.
- Emails, coupon codes, invoice numbers, and money amounts that must stay in Latin digits are wrapped so their internal order stays left-to-right inside the RTL page (`dir="ltr"` on that element).
- Font is Noto Sans Arabic for the UI. The PDF uses Noto Naskh Arabic.
- Theme: `dark` class on `<html>`, Tailwind `dark:` variants, both themes defined for surface, text, border, and danger/success states. The toggle labels are الوضع الليلي and الوضع النهاري. First visit uses light mode. The choice is stored under `localStorage` key `theme`.
- Every phase checklist includes 360, 768, 1024, and 1440, in both themes, with a short Arabic string and a long Arabic string so wrapping is visible.
- A 1920px glance is included on dashboard pages so the sidebar layout still aligns and lines do not stretch across the whole monitor without the container rule.

---

## 9. Company isolation and the three roles

Isolation is enforced in the service layer, with the role taken from the token. The UI hides links; the API rejects the call even if the UI is bypassed.

### 9.1 Rules

| Actor | Company id source | What they may touch |
| --- | --- | --- |
| Platform Admin | None. The token’s `company_id` is null. | Join decisions, create a company and its one manager, suspend/stop, platform-wide aggregates, platform settings, platform-targeted complaints. |
| Company Manager | `company_id` claim only. | Packages, coupons, clients, subscriptions, sales, profits, and complaints of that one company. |
| Client | The company id they select, checked on each call. | Available companies, that company’s packages, own purchases, own subscriptions, own invoices, own complaints, own expiry notices. |

- Manager routes do not take `company_id` from the query or body. The service receives it from `deps.py`.
- A client-supplied `company_id` is accepted only on company listing details, package listing, purchase, and a company-targeted complaint. The service loads the company and applies the status rule and the “deals with” rule.
- A manager token presented to an admin route receives 403.
- An admin token presented to `/api/company/...` receives 403. The admin does not manage a company’s packages, coupons, or clients.
- A client token presented to manager or admin routes receives 403.
- A row that belongs to another company returns 404 from the owning role’s routes.
- List queries include `company_id` (manager) or `client_id` (client) in the same query that loads the rows.

### 9.2 Tests that every data-owning phase repeats

Using Company A and Company B:

- Manager A lists data and receives only A.
- Manager A requests B’s object id and receives 404.
- The admin token on a company-manager route receives 403.
- The client token on a manager route receives 403.
- The client sees only their own subscriptions, invoices, complaints, and notices.

### 9.3 Permission matrix

| Capability | Client | Company Manager | Platform Admin |
| --- | --- | --- | --- |
| Register | Yes | No | No |
| Log in / log out | Yes | Yes | Yes |
| Light / dark toggle | Yes | Yes, same website shell | Yes, same website shell |
| Choose a company and see its packages | Yes, approved companies | No | No |
| Buy and see own history | Yes | No | No |
| Apply a coupon at purchase | Yes, that company only | No | No |
| Receive purchase email and PDF | Yes | Download of that company’s invoices | No |
| Expiry notice | Yes | No | No |
| Submit complaint or support request | Yes | No | No |
| Create / edit / delete packages | No | Own company | No |
| Create coupons | No | Own company | No |
| Follow clients and subscriptions | No | Own company | No |
| Activate, renew, review, stop subscriptions | Renew own, once defined | Own company, once defined | No |
| Sales and profits | No | Own company | No |
| Reply to company complaints | No | Own company | No |
| Create manager accounts | No | No | Yes |
| Approve or reject join requests | No | No | Yes |
| Suspend or stop a company | No | No | Yes |
| Platform performance | No | No | Yes |
| Platform settings | No | No | Yes |
| Follow platform complaints | No | No | Yes |

---

## 10. Moving from SQLite to PostgreSQL

The application chooses the database only through `DATABASE_URL`. Feature code uses the SQLAlchemy session and does not branch on the driver.

Development:

```text
DATABASE_URL=sqlite:///./backend/dev.db
```

Production:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/eshtrakei
```

Switch steps:

1. Keep migrations on the portable types listed in section 6.6.
2. Create an empty PostgreSQL database.
3. Set `DATABASE_URL` to the PostgreSQL URL in the production environment.
4. Run `alembic upgrade head` against that URL.
5. Run `python -m backend.scripts.seed_admin` with the production admin email and password.
6. Start the API. No file in `auth`, `companies`, or any other feature is edited for the switch.

`db.py` applies the SQLite foreign-key pragma only when the URL scheme is SQLite. PostgreSQL enforces foreign keys without that pragma.

Before the first production cutover, run the Phase 0 through Phase 12 pytest suite once with a PostgreSQL `DATABASE_URL` and once with SQLite. The suite is the check that the migrations and queries stay portable.

Development rows in `dev.db` are not part of the production launch. Production starts empty, then the admin seed runs. Copying the SQLite file into PostgreSQL is outside this plan.

---

## 11. Open questions

These are unspecified in the system description. The plan does not pick an answer for them. The phase named on each question is blocked on that answer, as written in section 5.

1. **Company join intake** (blocks approve/reject wiring in Phase 2). Who submits a join request, and through which channel? The admin’s approve/reject duty and the admin’s separate duty to create the manager account are both already in the plan. The missing piece is how a request becomes a `pending` row.

2. **Suspend versus stop** (blocks the two admin actions in Phase 2). Is تعليق a different status from إيقاف? After either action, what happens to subscriptions that are already active, and can that company’s manager still log in? The client list already hides any company that is not `approved`, and new purchases are already refused.

3. **Package fields** (blocks Phase 3). What is the unit of المدة (days, months, or another unit)? Are الحجم and السرعة free text the manager writes, or numbers with fixed units? When the manager deletes a package that already has subscriptions, is the delete refused, or is the package hidden from new purchases while old subscriptions remain?

4. **Coupon rules** (blocks Phase 4 and coupon math in Phase 6). For a coupon: percentage or fixed amount, the value, whether it expires, how many times it can be used, and whether one client can use it once or many times. Can a coupon be used when renewing, or only on a new purchase? The word used next to coupons in the full function list is عند الشراء.

5. **Renewal and overlapping subscriptions** (blocks renewal in Phase 6). Does renewal extend the same subscription’s end date, or create a new subscription row and a new invoice? A client can already hold subscriptions with different companies. May that client also hold two active subscriptions with the same company at the same time?

6. **Manager actions on a subscription** (blocks activate, review, and stop in Phase 6). The stored statuses named in the data model are active and expired. What does تفعيل do if a successful purchase is already active? What does إيقاف do: set the subscription to expired immediately, or store another status? What does مراجعة require beyond opening the subscription record, which is already how the manager follows a subscription?

7. **Currency** (blocks Phase 5). Which currency code is stored on payments and printed on the invoice?

8. **Expiry notice** (blocks Phase 8). How many days before `end_date` is “approaching”? Which timezone defines “today”? Is the in-app notice enough, or is an email required as well? The purchase confirmation email stays required either way.

9. **Complaints** (blocks Phase 9). Which companies may a client target: only companies with an active subscription, or any company they have ever subscribed to? After the company manager replies, can the client see that reply? The admin duty is متابعة of platform-directed complaints. Does the admin also reply, or only view them?

10. **Profits and platform performance** (blocks the profit figure in Phase 10 and all of Phase 11). How is الربح calculated from the data this system has? Which totals must appear on the platform performance screen? Sales for one company are already defined as the sum of that company’s successful payments. Platform figures must be aggregates across companies and must stay free of another company’s private rows.

11. **General settings** (blocks Phase 12). List each setting key, what it changes, its default, and which roles may read it. Until that list exists, no settings are invented.

12. **Client registration** (blocks Phase 1). Which fields does the client submit besides email and password? A name is required on the invoice, so `full_name` is included unless you say the invoice should show something else. What is the password rule?

13. **Email or PDF failure** (blocks calling Phase 7 done). If the mock payment succeeded and the subscription was stored, and then the PDF or the confirmation email fails, should the purchase stay successful, or should the whole purchase be cancelled?

14. **Company profile** (does not block a phase unless you want more than a name). The client list shows the company name. Should a company also have a description, phone, logo, or any other field?

### Suggested order to answer

Phase 0 can start before these answers. Phase 1 needs question 12. Phase 2 needs questions 1 and 2 for its blocked parts, and question 14 only if the company list should show more than a name. Later phases need the question cited on that phase. Answers can all be given up front so no phase waits.
