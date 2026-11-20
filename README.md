# NutriLens — From Laboratory Insights to Personalized Nutrition

**Evidence-Based Nutrition Support Platform**  
AI & Clinical Biomarker Intelligence System  

---

## 🌿 Overview
**NutriLens** is an evidence-grounded nutrition-support platform that transforms laboratory blood biomarkers into practical, culturally relevant Indian food recommendations. It strictly adheres to individual dietary preferences and allergies without making clinical diagnoses.

### The 4 Core Pillars
1. **Report Intelligence:** Dual-layer extraction (`pdfplumber` layout-aware extraction + Gemini Flash structured JSON fallback) paired with local **PII de-identification** and a **Human-in-the-Loop Confirmation Screen**.
2. **Biomarker Intelligence & Lab Interval Preservation:** Strict unit normalization (e.g., `ng/mL` vs `nmol/L`, `pg/mL` vs `pmol/L`) and deterministic classification that **strictly preserves the reporting laboratory's reference range** without silent overwrite. Separate clinical guideline thresholds (e.g., Lipid Association of India / NCEP ATP III for LDL $<100$ mg/dL; ICMR/ADA for HbA1c and glucose) are distinctly badged with source citations.
3. **Nutrition Intelligence & Regional Meal Planner:** Google OR-Tools constraint solver generating balanced regional Indian meal plans (Familiar, Most Nutritious, Regional) parameterized with **ICMR-NIN (2020) Dietary Guidelines**. Features realistic household portions, starch-stacking prevention, transparent shortfall accounting (reporting actual intake vs. target for low nutrients such as Vitamin D), and dynamic dish swaps that rebuild the shopping list.
4. **Personalization & Zero-Tolerance Allergen Guardrails:** Hard constraint satisfaction for dietary types (`Vegetarian`, `Vegan`, `Eggetarian`, `Non-Vegetarian` with **total elimination of beef and pork**) and allergens (`Dairy`, `Gluten`, `Nuts / Tree nuts & Peanuts`, `Soy`, `Eggs`, `Seafood`, `Mustard`, `Sesame`). Allergen exclusions are strictly enforced across recipes, garnishes, cooking ingredients, swaps, shopping lists, and free-text tips. Historic saved reports actively flag conflicts with active allergy profiles and provide safe regeneration.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│     Client UI (React 19 + Vite + Tailwind CSS)         │
│  • Drag & Drop PDF Ingestion & OCR Preview             │
│  • Human-in-the-Loop Verification Table                │
│  • Range Gauges with Preserved Lab Intervals           │
│  • Clinical Guideline Badges (LAI / ICMR / ADA)        │
│  • Regional Meal Planner (Familiar, Nutritious, Region)│
│  • Dish Swap & Dynamic Shopping List Sync              │
│  • Target vs. Intake Shortfall Accounting              │
│  • Saved Report Allergen Conflict Detection Banner     │
└───────────────────────────┬────────────────────────────┘
                            │ REST API / Multipart
                            ▼
┌────────────────────────────────────────────────────────┐
│               FastAPI Backend Pipeline                 │
│                                                        │
│  1. Ingestion & Privacy Layer                          │
│     • pdfplumber layout & table parser                 │
│     • Local PII Sanitizer (Regex scrubbing)            │
│     • Regex Matcher with alias resolution              │
│     • Gemini 2.5 Flash JSON fallback                   │
│                                                        │
│  2. Biomarker Intelligence Engine                      │
│     • Unit Normalization (Canonical conversions)       │
│     • Lab Range Preservation (Report Range intact)     │
│     • Guideline Threshold Evaluation (LAI, ADA, ICMR)  │
│     • Status Classifier (Low | Borderline | Normal)    │
│                                                        │
│  3. Nutrition & Meal Planning Engine (OR-Tools)        │
│     • ICMR-NIN 2020 Energy (Schofield) & PAL Mapping   │
│     • Protein RDA (0.83 g/kg body weight)              │
│     • Deep Allergen Validator (Tree nuts & peanuts)    │
│     • Starch-Stacking Penalty & Realistic Portions     │
│     • Dish Swap Mechanics & Shopping List Rebuilder    │
│     • Transparent Shortfall Reporter (e.g. Vitamin D)  │
│     • Absorption Tip Sanitizer (Zero text leak)        │
│                                                        │
│  4. Delivery & Export Layer                            │
│     • Deterministic Grounded Narrative Generator       │
│     • ReportLab Downloadable Branded A4 PDF            │
│     • Private per-user history (Neon PostgreSQL)       │
│     • Accounts, roles & audit log (owner/admin/user)   │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- Node.js 20.19+, 22.13+ or 24+ (includes DOM test support)

### 1. Backend Setup
```bash
# from the project root
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # then paste your Neon DATABASE_URL into backend/.env
```
Without a `DATABASE_URL`, the backend uses a local SQLite file (`backend/nutrilens.db`) for offline development.
Database tables are created and upgraded automatically (Alembic migrations) when the server starts.

Create the single **owner** account (once per database):
```bash
cd backend
python -m app.cli create-owner --email you@example.com --name "Your Name"
```

Run the app (API + built frontend on one port):
```bash
python run.py
```
- Interactive UI: [http://localhost:8000/](http://localhost:8000/) *(serves the production build in `frontend/dist`)*
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Development Setup
```bash
cd frontend
npm install
npm run dev
```
- Frontend Dev Server: [http://localhost:5173/](http://localhost:5173/) *(proxies `/api` to port 8000)*

### 3. Build Frontend for Production
```bash
cd frontend
npm run build
```
The compiled SPA is output to `frontend/dist/` and automatically served by FastAPI at `http://localhost:8000/`.

---

## 🧪 Running Tests

```bash
.venv/bin/python -m pytest -q          # backend: extraction, rules, auth, roles, ownership, admin
cd frontend && npm test                # frontend: profile form, login, role-based navigation, full flow
```
Backend tests always use a throwaway in-memory database, never the real one.

---

## 📡 API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/v1/extract-report` | Anyone | Upload PDF/image or paste text; scrubs PII and extracts biomarkers. |
| `POST` | `/api/v1/analyze-and-recommend` | Anyone | Returns personalized nutrition plan and preserved biomarker intervals. |
| `POST` | `/api/v1/diet-plan/options` | Anyone | Computes 3 personalized daily meal options (Familiar, Nutritious, Regional) via OR-Tools. |
| `POST` | `/api/v1/diet-plan/week` | Anyone | Solves a balanced 7-day regional meal plan and generates aggregated shopping list. |
| `POST` | `/api/v1/diet-plan/swap` | Anyone | Replaces a dish, revalidates constraints, updates nutrient totals and shortfalls. |
| `POST` | `/api/v1/diet-plan/shopping-list` | Anyone | Rebuilds purchase-weight shopping list dynamically from updated meal plans. |
| `POST` | `/api/v1/diet-plan/pdf` | Anyone | Generates a branded A4 PDF of the 7-day meal plan and categorized shopping list. |
| `POST` | `/api/v1/export-plan-pdf` | Anyone | Renders biomarker review and dietary advice as a comprehensive medical PDF. |
| `POST` | `/api/v1/auth/register` · `/login` · `/logout` | Anyone | Account sign-up and sessions (HttpOnly cookie). |
| `GET` | `/api/v1/auth/session` · `/auth/me` | Anyone / signed in | Who is signed in. |
| `PATCH`/`POST` | `/api/v1/auth/me` · `/change-password` · `/delete-account` | Signed in | Self-service account management. |
| `GET`/`POST` | `/api/v1/auth/invites/{token}` · `/auth/reset/{token}` | Link holder | One-time invitation and password-reset links. |
| `GET`/`DELETE` | `/api/v1/history` · `/history/{id}` | Signed in | Your own saved reports only (others' return 404). |
| `GET`/`PATCH`/`POST`/`DELETE` | `/api/v1/admin/users…` · `/admin/invites…` · `/admin/stats` · `/admin/audit-logs` | Admin, owner | User management, invitations, dashboard, audit log. |
| `POST`/`DELETE` | `/api/v1/admin/access…` · `/admin/transfer-ownership` | Owner | Grant/remove admin access, hand over ownership. |
| `GET` | `/api/health` | Anyone | Health check (never touches the database). |
| `GET` | `/docs` | Anyone | Interactive Swagger UI. |

---

## 📐 Clinical Guidelines & ICMR-NIN (2020) Reference Standards

NutriLens grounds all nutritional targets and biomarker evaluations in verified authoritative standards:

### 1. Energy Requirements & Physical Activity Levels (PAL)
Energy targets are derived from **ICMR-NIN (2020) Recommended Dietary Allowances for Indians** (Chapter 2 & Table 2.2):
- **Basal Metabolic Rate (BMR):** FAO/WHO/UNU (Schofield) equations adopted by ICMR-NIN:
  - Adult Male (18–29 y): $\text{BMR} = 15.3 \times \text{Weight (kg)} + 679\text{ kcal/day}$
  - Adult Female (18–29 y): $\text{BMR} = 14.7 \times \text{Weight (kg)} + 496\text{ kcal/day}$
  - Adult Male (30–59 y): $\text{BMR} = 11.6 \times \text{Weight (kg)} + 879\text{ kcal/day}$
  - Adult Female (30–59 y): $\text{BMR} = 8.7 \times \text{Weight (kg)} + 829\text{ kcal/day}$
- **Activity Factor Mapping:**
  - **Sedentary (`"none"` / desk job / mostly sitting):** $\text{PAL} = 1.26$ (Male), $1.30$ (Female)  
    *(Matches ICMR-NIN Reference Indian Sedentary Man 65 kg $\rightarrow 2,110\text{ kcal/day}$ and Woman 55 kg $\rightarrow 1,660\text{ kcal/day}$)*
  - **Light Active (`"walking"`):** $\text{PAL} = 1.50$
  - **Moderate Active (`"cycling"`):** $\text{PAL} = 1.62$ (Male $\rightarrow 2,710\text{ kcal/day}$), $1.66$ (Female $\rightarrow 2,130\text{ kcal/day}$)
  - **Heavy Active (`"running"`):** $\text{PAL} = 2.00$ (Male $\rightarrow 3,350\text{ kcal/day}$), $2.12$ (Female $\rightarrow 2,560\text{ kcal/day}$)

### 2. Protein Target
- **Adult Protein RDA:** $0.83\text{ g per kg body weight per day}$ per ICMR-NIN 2020 (Reference Man 65 kg $\rightarrow 54.0\text{ g/day}$).

### 3. Preserved Lab Intervals vs. Clinical Guideline Thresholds
- **Reporting Lab Range:** Always preserved intact across all screens, history, and PDF exports.
- **Lipid Targets:** Evaluated against **Lipid Association of India (LAI 2020)** & NCEP ATP III:
  - LDL Cholesterol: Optimal $<100\text{ mg/dL}$, Borderline $100\text{--}159\text{ mg/dL}$, High $\ge 160\text{ mg/dL}$.
  - Total Cholesterol: Normal $<200\text{ mg/dL}$, Borderline $200\text{--}239\text{ mg/dL}$, High $\ge 240\text{ mg/dL}$.
  - Triglycerides: Normal $<150\text{ mg/dL}$, Borderline $150\text{--}199\text{ mg/dL}$, High $\ge 200\text{ mg/dL}$.
- **Glycemic Markers:** Evaluated against **ICMR Guidelines for Type 2 Diabetes (2023)** & ADA (2024):
  - Fasting Glucose: Normal $<100\text{ mg/dL}$, Impaired $100\text{--}125\text{ mg/dL}$, Diabetic $\ge 126\text{ mg/dL}$.
  - HbA1c: Normal $<5.7\%$, Prediabetic $5.7\text{--}6.4\%$, Diabetic $\ge 6.5\%$.

### 4. Transparent Shortfall Accounting
Natural whole-food Indian vegetarian diets rarely meet the $600\text{ IU}$ Vitamin D RDA solely through food (providing $\sim 42\text{--}127\text{ IU}$). NutriLens transparently reports actual intake vs. target and explicitly displays the shortfall with clinical guidance for safe sunlight exposure or medical supplementation, replacing unrealistic blanket claims.

---

---

## 📄 License & Safety
NutriLens is an educational nutrition-support tool and does not provide clinical diagnoses or prescription drug advice.


## Report formats and OCR

The existing upload flow accepts printed PDF, JPG/JPEG and PNG reports, plus pasted text. Native PDF extraction remains local with pdfplumber; insufficient pages use local Tesseract OCR. Install `tesseract` (macOS: `brew install tesseract`; Debian/Ubuntu: `apt-get install tesseract-ocr`) with English data, then install `backend/requirements.txt`.

Default limits are 10 MiB, 20 PDF pages, 20 million image pixels and 90 seconds per report. All are configurable in `backend/app/config.py` through uppercase environment settings. Deploy with proxy body-size and container memory limits. Handwriting and universal mobile-camera compatibility are not supported claims.

Review every extracted value and unit, resolve duplicates, and confirm the verification checkbox before continuing. Missing units, qualified bounds and conflicts are surfaced rather than silently corrected. Gemini receives only allowlisted clinical tokens, never raw images; this intentionally limits recovery of ambiguous rows.


## Age input

Age starts at 25, can be cleared during editing, and must be a whole number from 1–120 before submission.
Frontend regression tests: `cd frontend && npm test`.

## Accounts, roles & saved history

| Role | Who | Can do |
|---|---|---|
| **Guest** | Not signed in | Analyze a report, download the PDF. Nothing is saved. |
| **User** | Anyone who signs up | Everything a guest can, plus a private history of their analyses, account settings, delete account. |
| **Admin** | Invited or promoted by the owner | Everything a user can, plus the admin portal: dashboard, manage *users* (edit, disable, unlock, sign out, reset link, delete), invite users, audit log. Cannot change other admins or the owner. |
| **Owner** | Exactly one, created with `python -m app.cli create-owner` | Everything an admin can, plus add admins by email (promote or one-time invite link), edit/disable/remove admins, issue their reset links, and transfer ownership. |

- **Only one owner** is enforced by the database itself (a partial unique index), not just the code.
- **Nobody, including admins and the owner, can read another person's medical reports.** Admin views show account metadata and counts only.
- Passwords are hashed with Argon2id. Sessions are random tokens in an HttpOnly, SameSite cookie (7 days), revoked on logout, password change, disable or reset. Changes require a CSRF header. 5 failed logins lock an account for 15 minutes.
- Invitation and password-reset links are single-use, expire after 48 hours and are stored only as hashes. No email service is needed: admins copy the link and send it themselves.
- Every security-relevant action (sign-ins, failed logins, role changes, invites, resets, deletions) is written to the audit log.
- Lost owner password: `python -m app.cli set-password --email you@example.com` (run with the production `DATABASE_URL`).

## Deployment (Vercel + Render + Neon, all free tiers)

| Part | Host | Notes |
|---|---|---|
| Database | **Neon** Postgres, Singapore | Use the *pooled* connection string as `DATABASE_URL`. |
| API | **Render** web service (Docker, `backend/Dockerfile`), Singapore | Env vars: `DATABASE_URL`, `COOKIE_SECURE=true`, optional `GEMINI_API_KEY` and `GROQ_API_KEY` (free; assistant answers in natural language). Sleeps after 15 min idle (first request ~30–60 s). |
| Frontend | **Vercel**, root directory `frontend` | `frontend/vercel.json` forwards `/api/*` to the Render URL, so the browser sees one domain and login cookies stay first-party. |

After the first deploy, create the owner from your laptop against the production database:
`cd backend && DATABASE_URL="<neon url>" python -m app.cli create-owner --email you@example.com --name "Your Name"`.
