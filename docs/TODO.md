# OAS Bay — Build Checklist

Working plan for building the project by Monday. Check items off as you go. Reference docs: [PRD.md](./PRD.md), [project-brief.md](./project-brief.md).

---

## Phase 1 — Project skeleton & data layer (Done)

- [x] Virtual environment created, Django 6.1 installed in it
- [x] Project `oas_bay` + apps `core`, `inventory`, `operations` created
- [x] `settings.py` configured — apps registered, `TEMPLATES.DIRS`, `TIME_ZONE = Africa/Kampala`, `LOGIN_URL`/`LOGIN_REDIRECT_URL`
- [x] Models written: `Customer`, `Vehicle` (core); `Service`, `SparePart`, `InventoryTransaction` (inventory); `JobCard`, `JobCardServiceLine`, `JobCardPartLine`, `Payment` (operations)
- [x] Migrations generated and applied — `db.sqlite3` created
- [x] All models registered in Django admin, with inlines on `Customer` (vehicles) and `JobCard` (service lines, part lines, payments)
- [x] Stock auto-deducts on `JobCardPartLine` save, logging an `InventoryTransaction`
- [x] Groups seeded: `Admin`, `Senior Technician`, `Junior Technician`, each with real model permissions
- [x] Catalog seeded: all 8 services, all 6 spare parts, confirmed prices
- [x] `python manage.py check` clean, dev server confirmed serving `/admin/`

**Still needed from you to close this phase:**
- [ ] Run `python manage.py createsuperuser` and log into `/admin/` yourself to confirm it feels right

---

## Phase 2 — Core workflow (views & templates) (Done)

This is the actual assignment — the part that isn't just Django admin.

### 2.1 Base layout
- [x] `templates/base.html` — navbar, Bootstrap 5 + Bootstrap Icons via CDN, `crispy_forms` wired up, block for page content, shows logged-in user + their group(s)
- [x] `static/css/theme.css` — midnight blue (`#14163A`) + vanilla (`#F3E9D2`) theme layered over Bootstrap: navbar, cards, buttons, table headers, status badges, receipt print styling

### 2.2 Customers & vehicles
- [x] List/search view for customers (by name, phone, plate number — FR-3)
- [x] Create customer form (crispy)
- [x] Add vehicle to a customer form (crispy)
- [x] Customer detail page showing all their vehicles
- [x] Vehicle detail page showing its full job card history (FR-2, FR-18)

### 2.3 Job card creation flow
- [x] "New job card" view, customer preselected, vehicle optional/prefilled via `?vehicle=`
- [x] Set `visit_type` (service / parts / both)
- [x] Diagnosis notes field, auto-fills `diagnosed_by` = current user
- [x] Add service line(s) to a job card (dropdown of active `Service` + auto-filled price)
- [x] Add part line(s) to a job card (dropdown of active `SparePart`, quantity input, auto-filled price, stock check via form validation)
- [x] Assign one or more technicians (`assigned_technicians` multi-select — FR-5)
- [x] Job card detail page showing lines, running total, balance, status

### 2.4 Payments
- [x] Record payment form on a job card (amount, method: cash / MTN / Airtel — FR-14)
- [x] Show balance remaining after each payment; form rejects overpayment
- [x] Mark job card `paid` automatically when balance reaches 0
- [x] Printable receipt page per payment (`@media print` CSS — FR-15)

### 2.5 Job card status
- [x] Status transitions: `open` → `in_progress` → `completed` → `paid` (manual dropdown on job card detail)
- [ ] Junior technician restricted to only updating cards they're assigned to — **moved to Phase 3**, needs group-based view logic

**Checkpoint — verified:** ran the full golden path programmatically (customer → vehicle → job card → diagnosis → service line → part line → payment → receipt) against the real views. All pages returned 200, stock deducted correctly on the part line, job card auto-flipped to `paid` at zero balance. Every page loads with the midnight blue / vanilla theme.

---

## Phase 3 — Auth, roles, reporting, polish

### 3.1 Auth
- [x] Login page (`templates/registration/login.html`), styled with the theme
- [x] Logout view wired up (`django.contrib.auth.urls`, POST-only per Django 6.1)
- [ ] Navbar/menu items shown/hidden based on group membership — currently every logged-in user sees the same nav (only the Admin link is gated on `is_staff`)
- [ ] Restrict views with `@permission_required` / group checks — currently every view only requires `@login_required`, so any logged-in user can do anything (e.g. a Junior Technician can currently record payments)
- [ ] Junior technician limited to cards they're assigned to (carried over from 2.5)

### 3.2 Reporting / dashboard
- [x] Dashboard view: today's revenue (`Payment` aggregate)
- [x] Most-performed services (FR-17 — count `JobCardServiceLine` grouped by service)
- [x] Low-stock spare parts list (`SparePart.is_low_stock` — FR-11, FR-19)
- [x] Bootstrap cards/list-group layout for the above, theme-styled

### 3.3 Polish
- [ ] Form validation errors display cleanly (Bootstrap alert/invalid-feedback styling)
- [ ] Empty states (no customers yet, no job cards yet) don't look broken
- [ ] Confirm currency displays as `UGX 20,000` formatting consistently
- [ ] Mobile-responsive check (Bootstrap grid, no horizontal scroll)

---

## Phase 4 — Final QA & submission prep

- [ ] Walk the golden path logged in as **Admin**
- [ ] Walk the golden path logged in as **Senior Technician**
- [ ] Walk the golden path logged in as **Junior Technician** — confirm restrictions actually hold
- [ ] Test a parts-only sale (no vehicle, optional customer)
- [ ] Test a partial payment, confirm balance and status update correctly
- [ ] Test low-stock flag by depleting a part's stock
- [ ] `python manage.py check` and a fresh `migrate` on a clean clone still work
- [ ] Seed demo data is realistic and ready for a live demo (re-run `seed_data`, add a few sample customers/vehicles/job cards)
- [ ] Short `README.md` at project root: setup steps (`venv`, `pip install`, `migrate`, `createsuperuser`, `runserver`), and which login/role to demo with
- [ ] Remove/hide the Django secret key from version control if pushing to GitHub (`.gitignore` for `venv/`, `db.sqlite3`, `__pycache__/`)

---

## Definition of done

- [ ] Every functional requirement in [PRD.md §6](./PRD.md#6-functional-requirements) has a working screen or admin path
- [ ] All three roles behave differently and correctly
- [ ] The app looks intentional (Bootstrap-styled, no unstyled default forms) without having spent time on custom CSS
- [ ] You can demo it cold, live, without touching the database by hand
