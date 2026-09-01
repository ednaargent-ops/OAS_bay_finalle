# AutoShop Manager — Product Requirements Document

**Project:** Oyera Auto Service Bay Ltd (OAS Bay) — Records Management System
**Stack:** Python / Django
**Currency:** UGX (Uganda Shillings)
**Version:** 0.3 — Draft, pricing confirmed, scoped to course level
**Source of truth:** [project-brief.md](./project-brief.md)

---

## 1. Overview

The shop currently has no system to track who came in, what was done to which vehicle, what parts were used, what was charged, and what's left in stock. This product replaces that gap with a single internal tool covering the full life of a visit — from a customer walking in, to diagnosis, to the technicians doing the work, to payment.

A customer can own several vehicles, and each vehicle keeps its own independent service history — e.g. Peter's Hilux and Peter's Mercedes-Benz are tracked separately under the same customer record, since they need different services at different intervals.

---

## 2. Goals & Scope

**In scope for v1**

- Customer and per-vehicle service history
- Job cards: diagnosis → technician assignment → work → payment
- Three visit types: service only, parts only, or both
- Service catalog with labour pricing (per the brief's flat-rate model)
- Spare-parts inventory with stock levels
- Payments, partial payments, and receipts
- Role-based staff accounts

**Explicitly out for v1**

- Payroll / salaries
- General expense ledger (rent, utilities)
- Multiple shop locations
- Supplier management
- SMS / email notifications

---

## 3. Users & Roles

The brief only names a **senior technician**, who determines parts/oils needed and (per your own description of how the shop runs) diagnoses the job. It also states **"one technician or more can handle a car service"** — so unlike a single junior-tech handoff, a job's actual work can be split across multiple technicians. The role split below keeps your real-world description (senior vs. junior) as a permissions layer on top of that.

| Role | Responsibilities |
|---|---|
| **Admin / Owner** | Manage staff accounts, edit service catalog and prices, edit spare-parts catalog and cost/selling price, record inventory restocks, view all job cards/payments/reports |
| **Senior Technician** | Open a job card, determine parts/oils needed, record diagnosis, assign one or more technicians to the work, mark a job card complete, record payments and issue receipts |
| **Junior Technician** | View job cards they're assigned to (one card can have several technicians), update status/work notes on their own assigned cards, cannot open new job cards, cannot take payment, cannot see prices or inventory cost |

*Confirm: should a junior technician be allowed to see prices or take payment? Current default says no.*

**Implementation note:** roles are implemented as three Django `auth.Group`s — `Admin`, `Senior Technician`, `Junior Technician` — using Django's built-in Groups & permissions system rather than a custom role field.

---

## 4. Core Workflow

1. **Customer arrives, job card opened** — customer and vehicle are looked up or created. Visit type is set: service, parts only, or both.
2. **Parts & diagnosis** — the senior technician determines what parts/oils are needed and the owner buys them; diagnosis notes are recorded on the job card.
3. **Assignment** — the senior technician assigns **one or more** technicians to carry out the work.
4. **Work performed** — each service actually carried out is logged as its own line (e.g. Engine Oil Change, Wheel Alignment); each part consumed is logged as its own line and deducted from stock.
5. **Payment** — total = sum of service lines + sum of part lines. Payment can be full or partial; a receipt is generated per payment, and balance owed is tracked until fully paid.

**Worked example:** Peter brings his Hilux in for an oil change. The senior technician determines it needs 1 unit of engine oil and 1 oil filter, which Peter buys. A technician performs the change. The job card ends up with:

- Service line: **Engine Oil Change — labour 20,000 UGX**
- Part line: **Engine Oil ×1 — e.g. 95,000 UGX** (within the 79,000–200,000 range)
- Part line: **Oil Filter ×1 — e.g. 18,000 UGX** (within the 15,000–20,000 range)

Combined total is charged, which Peter can pay in full or in part, each payment producing its own receipt.

---

## 5. Data Model

### Customer

| Field | Type | Notes |
|---|---|---|
| full_name | CharField | Required |
| phone | CharField | Required, used to look up returning customers |
| email | EmailField | Optional |
| created_at | DateTimeField | Auto |

### Vehicle

| Field | Type | Notes |
|---|---|---|
| customer | FK → Customer | One customer, many vehicles |
| make | CharField | e.g. Toyota, Mercedes-Benz |
| model | CharField | e.g. Hilux |
| plate_number | CharField | Unique |
| duty_class | Choice | `heavy_duty` / `light_duty` / `commercial` — brief mentions heavy, small, and commercial cars |
| year | IntegerField | Optional |

### Service

Per the brief, most services share one flat labour price; alignment and balancing are priced separately. Keeping each as its own `Service` row (rather than one generic "labour" row) preserves the ability to count how often each service is performed (FR-7).

| Field | Type | Notes |
|---|---|---|
| name | CharField | e.g. Engine Oil Change, Gearbox Oil Change, Brake Fluid Change, Brake Pad Change, Greasing, Minor Repair, Wheel Alignment, Wheel Balancing |
| labor_price | DecimalField | UGX — 20,000 for standard services; 30,000 for alignment; 20,000 for balancing |
| active | BooleanField | To retire a service without deleting history |

### SparePart

| Field | Type | Notes |
|---|---|---|
| name | CharField | e.g. Engine Oil, Gearbox Oil, Oil Filter, Gearbox Oil Filter, Brake Fluid, Brake Pad |
| category | CharField / FK | e.g. Oils, Filters, Brake Parts |
| cost_price | DecimalField | What the shop paid |
| selling_price | DecimalField | What the customer is charged — engine oil 79,000–200,000, oil filter 15,000–20,000, brake fluid 13,000–20,000, gearbox oil 30,000, gearbox oil filter 50,000, brake pad 35,000 (all confirmed — see [project-brief.md](./project-brief.md)) |
| quantity_in_stock | IntegerField | Decremented on every sale/use |
| reorder_level | IntegerField | Flag low stock below this |

### JobCard

| Field | Type | Notes |
|---|---|---|
| customer | FK → Customer | Required for service visits; optional for parts-only |
| vehicle | FK → Vehicle, null=True | Blank for a pure parts-only sale with no vehicle context |
| visit_type | Choice | `service` / `parts` / `both` |
| diagnosis_notes | TextField | Set by senior technician |
| diagnosed_by | FK → User | Senior technician |
| assigned_technicians | **ManyToManyField → User** | One or more technicians — updated from a single FK, per the brief |
| status | Choice | `open` / `in_progress` / `completed` / `paid` |
| created_at / completed_at | DateTimeField | |

### JobCardServiceLine & JobCardPartLine

| Field | Type | Notes |
|---|---|---|
| job_card | FK → JobCard | |
| service / spare_part | FK | One line per service performed or part used |
| quantity | IntegerField | Parts lines only |
| price_charged | DecimalField | Snapshot at time of visit — so past job cards stay accurate if catalog prices change later |

### Payment

| Field | Type | Notes |
|---|---|---|
| job_card | FK → JobCard | |
| amount | DecimalField | One row per payment — supports partial/installment payments |
| method | Choice | `cash` / `mtn_mobile_money` / `airtel_money` |
| received_by | FK → User | |
| paid_at | DateTimeField | |

Balance owed = job card total − sum of its Payment rows. A receipt is generated per payment.

### InventoryTransaction

| Field | Type | Notes |
|---|---|---|
| spare_part | FK → SparePart | |
| type | Choice | `restock` (in) / `used` (out, tied to a job card) |
| quantity | IntegerField | |
| unit_cost | DecimalField | Restocks only — this is the "money out" for inventory |
| reference | FK → JobCard, null=True | Set when type=used |

---

## 6. Functional Requirements

**Customers & Vehicles**
- FR-1: Staff can register a customer and attach one or more vehicles to them.
- FR-2: Each vehicle has its own independent service history, viewable on its own.
- FR-3: Staff can look up a customer or vehicle by name, phone number, or plate number.

**Service Catalog & Job Cards**
- FR-4: Admin maintains the list of services and their labour prices.
- FR-5: A job card records visit type, diagnosis, the diagnosing senior technician, and one or more assigned technicians.
- FR-6: A job card can carry multiple service lines and multiple part lines.
- FR-7: The system counts how many times each service has been performed — overall, and per vehicle.

**Inventory / Spare Parts**
- FR-8: Admin maintains the spare parts catalog: name, category, cost price, selling price, stock quantity.
- FR-9: Using a part on a job card automatically deducts it from stock.
- FR-10: Restocking a part records the quantity and cost, and adds it back to stock.
- FR-11: Parts below their reorder level are flagged.
- FR-12: A customer may buy spare parts with no service performed. Customer can optionally be attached to that sale, but it's not required.

**Payments**
- FR-13: Job card total is computed as the sum of its service and part lines.
- FR-14: Payments can be partial; the system tracks balance remaining until fully paid.
- FR-15: A printable/shareable receipt is generated for each payment.

**Reporting**
- FR-16: Revenue totals by day / week / month.
- FR-17: Most-performed services and best-selling parts.
- FR-18: Full history per vehicle: every job card, service, part, and payment against it.
- FR-19: Current stock levels and low-stock list.

---

## 7. Non-Functional

- **Stack:** Django, using **SQLite** (Django's default) — deliberately kept rather than upgraded to PostgreSQL, since this is a 3-month junior-developer course project and the assessment is on what's actually been taught. SQLite is enough for a single shop with one or two people using it at a time.
- **Single location:** built for one shop, one set of inventory.
- **Currency:** UGX only; whole-shilling amounts (no decimals needed in daily use).
- **Timezone:** Africa/Kampala.
- **Auditability:** price on a job card line is a snapshot at time of sale, so editing a catalog price later never rewrites past records.

---

## 8. Assumptions

- One shop, one location.
- "Money out" for v1 means the cost of restocking spare parts only — not salaries or general shop expenses.
- A vehicle belongs to exactly one customer at a time.
- Junior and senior technician are permission levels, not a pay grade the system needs to model.
- Receipts are viewed/printed from the browser (PDF export) rather than emailed or SMS'd.
- A job card may have several technicians assigned to it (per the brief); work notes/status updates can come from any of them.
- This PRD is scoped to a 3-month junior-developer course. If any pattern here (e.g. the technicians many-to-many field, or snapshotting prices on job card lines) is beyond what your course has covered so far, say so and it can be simplified — the grading is on what you've actually learned, not on architectural completeness.

---

## 9. Open Questions

All pricing and payment-method gaps from the original brief are now resolved:

| Question | Answer |
|---|---|
| Gearbox oil price | 30,000 UGX |
| Gearbox oil filter price | 50,000 UGX |
| Brake pad price | 35,000 UGX |
| Brake fluid range | 13,000–20,000 UGX (confirmed) |
| Payment methods | Cash, MTN Mobile Money, Airtel Money — no bank transfer or card |

No open questions remain blocking the data model. See [project-brief.md](./project-brief.md) for the full confirmed pricing table.

---

## 10. Out of Scope (v1)

| Feature | Why it's deferred |
|---|---|
| Payroll / salaries | Not part of the "money out" definition — inventory restocking cost only, for now. |
| General expense ledger (rent, utilities, tools) | Same as above — a straightforward extra model to add later, not a redesign. |
| Supplier management | Restock cost is recorded, but not tied to a supplier record yet. |
| Multi-branch support | No second location mentioned. |
| SMS / email notifications | Not requested; receipts are print/PDF only for v1. |
