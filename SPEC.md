# NutriLens — Technical Specification & System Architecture
**Version:** 1.0.0  
**Authors:** NutriLens Engineering Team  
**System:** Clinical Nutrition & Biomarker Intelligence Platform  
**Architecture Track:** Production System Specification  

---

## 1. Executive Summary & Positioning

### 1.1 One-Line Positioning
**NutriLens:** *From laboratory insights to personalized nutrition.*  
An evidence-grounded nutrition-support platform that transforms laboratory blood biomarkers into practical, culturally relevant Indian food recommendations, strictly adhering to individual dietary preferences and allergies without making medical diagnoses.

### 1.2 Core Differentiation (The 4 Pillars)
1. **Report Intelligence:** Dual-layer extraction (`pdfplumber` layout-aware extraction + Gemini Flash structured JSON fallback) paired with **PII de-identification** and a **Human-in-the-Loop Confirmation Screen**.
2. **Biomarker Intelligence & Lab Interval Preservation:** Strict unit normalization (e.g., `ng/mL` vs `nmol/L`, `pg/mL` vs `pmol/L`) and deterministic classification that **strictly preserves the reporting laboratory's reference range** without silent overwrite. Separate clinical guideline thresholds (e.g., Lipid Association of India / NCEP ATP III for LDL $<100$ mg/dL; ICMR/ADA for HbA1c and glucose) are distinctly badged with source citations.
3. **Nutrition Intelligence & Regional Meal Planner:** Google OR-Tools constraint solver generating balanced regional Indian meal plans (Familiar, Most Nutritious, Regional) parameterized with **ICMR-NIN (2020) Dietary Guidelines**. Features realistic household portions, starch-stacking prevention, transparent shortfall accounting (reporting actual intake vs. target for low nutrients such as Vitamin D), and dynamic dish swaps that rebuild the shopping list.
4. **Personalization & Zero-Tolerance Allergen Guardrails:** Hard constraint satisfaction for dietary types (`Vegetarian`, `Vegan`, `Eggetarian`, `Non-Vegetarian` with **total elimination of beef and pork**) and allergens (`Dairy`, `Gluten`, `Nuts / Tree nuts & Peanuts`, `Soy`, `Eggs`, `Seafood`, `Mustard`, `Sesame`). Allergen exclusions are strictly enforced across recipes, garnishes, cooking ingredients, swaps, shopping lists, and free-text tips. Historic saved reports actively flag conflicts with active allergy profiles and provide safe regeneration.

---

## 2. System Architecture & Tech Stack

```
                          ┌─────────────────────────┐
                          │   Client Application    │
                          │ (React 19 + Vite + TW)  │
                          └───────────┬─────────────┘
                                      │ REST API / Multipart
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend Application                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Ingestion & Privacy Layer                                          │  │
│  │    • PDF Plumber Text & Table Extraction                              │  │
│  │    • PII Sanitizer (Regex scrubbing of Name, Phone, Email, Lab IDs)   │  │
│  │    • Regex Matcher with Alias Map                                     │  │
│  │    • LLM Fallback (Gemini Flash with Strict Pydantic JSON Schema)     │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 2. Biomarker Intelligence Engine                                      │  │
│  │    • Unit Normalization (Vit D ng/mL ↔ nmol/L, etc.)                  │  │
│  │    • Lab Range Preservation (Report Range intact)                     │  │
│  │    • Guideline Threshold Evaluation (LAI 2020, ICMR 2023, ADA 2024)   │  │
│  │    • Status Classifier (Low | Borderline | Normal | High)             │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 3. Nutrition Recommendation & Meal Planning Engine (OR-Tools)         │  │
│  │    • ICMR-NIN 2020 Energy (Schofield) & Sex-Specific PAL Mapping      │  │
│  │    • Protein Target (0.83 g/kg body weight/day)                       │  │
│  │    • Deep Allergen Validator (Composite 'Tree nuts & peanuts')        │  │
│  │    • Zero-Tolerance Beef & Pork Elimination                           │  │
│  │    • Realistic Regional Meal Planning (Starch-Stacking Penalty)       │  │
│  │    • Dish Swaps with Dynamic Shopping List Rebuild                    │  │
│  │    • Transparent Shortfall Reporter (Actual vs Target Accounting)     │  │
│  │    • Tip Sanitizer (Zero Allergen Leak in Absorption Advice)          │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 4. Grounded Explanation & Export Layer                                │  │
│  │    • Template + LLM Synthesis (strictly bounded by structured data)   │  │
│  │    • Clinical Advisory & Medical Disclaimer Injection                 │  │
│  │    • ReportLab Branded A4 PDF Generator (Lab & Meal Plan)             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Persistence: SQLite / PostgreSQL via SQLAlchemy (Audit Log, History)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Technology Stack Selection
- **Backend Framework:** FastAPI (Python 3.11+) — Async, high performance, native Pydantic typing, auto OpenAPI documentation.
- **Frontend Framework:** React 19 + Vite + Tailwind CSS + Lucide Icons — Ultra-responsive UI, visual range sliders, zero bloat.
- **Database:** SQLite with SQLAlchemy ORM — Zero external dependencies, self-contained for local viva demo.
- **PDF Extraction:** `pdfplumber` + Python `re` (regular expressions).
- **LLM Engine:** Gemini 2.5 Flash via official Google GenAI SDK (`google-genai`).
- **Data Validation:** Pydantic v2.
- **Test Framework:** `pytest` (rule engine unit tests, benchmark harness).
- **PDF Export:** `xhtml2pdf` or `reportlab` for downloadable client nutrition plans.

---

## 3. Data Schemas & Reference Standards

### 3.1 Target Biomarkers & Reference Standards

NutriLens maintains strict separation between **the reporting laboratory's reference range** (preserved intact) and **evidence-based clinical guideline thresholds** (displayed distinctly with source citations):

| Biomarker | Canonical Unit | Alternate Units | Alias Variations | Reporting Lab Interval | Clinical Guideline Threshold & Source |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Vitamin D (25-OH)** | `ng/mL` | `nmol/L` ($1\text{ ng/mL} = 2.5\text{ nmol/L}$) | Vit D, 25-OH Vitamin D, 25(OH)D | 30–100 ng/mL | Endocrine Society: Low $<20$, Borderline $20\text{--}29.9$ ng/mL |
| **Vitamin B12** | `pg/mL` | `pmol/L` ($1\text{ pg/mL} = 0.738\text{ pmol/L}$) | Vit B12, Cobalamin | 211–911 pg/mL | Low $<150$, Borderline $150\text{--}210$ pg/mL |
| **Folate (Vitamin B9)** | `ng/mL` | `nmol/L` ($1\text{ ng/mL} = 2.266\text{ nmol/L}$) | Folic Acid, Serum Folate | 4.0–20.0 ng/mL | WHO Guidelines: Low $<2.5$, Borderline $2.5\text{--}3.9$ ng/mL |
| **Serum Ferritin** | `ng/mL` | `µg/L` ($1\text{ ng/mL} = 1\text{ µg/L}$) | Ferritin, S. Ferritin | M: 24–336 ng/mL<br>F: 11–307 ng/mL | Iron deficiency: $<15$ ng/mL (Severe $<10$ ng/mL) |
| **Hemoglobin** | `g/dL` | `g/L` ($1\text{ g/dL} = 10\text{ g/L}$) | Hb, Hgb | M: 13.0–17.0 g/dL<br>F: 12.0–15.0 g/dL | WHO: Anemia $<12.0$ (F) / $<13.0$ (M) g/dL |
| **Serum Calcium** | `mg/dL` | `mmol/L` ($1\text{ mmol/L} = 4.008\text{ mg/dL}$) | Total Calcium, Ca | 8.5–10.2 mg/dL | Hypocalcemia $<8.0$, Borderline $8.0\text{--}8.4$ mg/dL |
| **LDL Cholesterol** | `mg/dL` | `mmol/L` ($1\text{ mmol/L} = 38.67\text{ mg/dL}$) | LDL, Bad Cholesterol | 0–129 mg/dL *(Lab reported)* | **LAI 2020 / NCEP ATP III:** Optimal $<100$, Borderline $100\text{--}159$, High $\ge 160$ mg/dL |
| **Total Cholesterol** | `mg/dL` | `mmol/L` | Cholesterol Total | 0–200 mg/dL *(Lab reported)* | **NCEP ATP III:** Desirable $<200$, Borderline $200\text{--}239$, High $\ge 240$ mg/dL |
| **Triglycerides** | `mg/dL` | `mmol/L` | Triglycerides, TG | 0–150 mg/dL *(Lab reported)* | **NCEP ATP III:** Normal $<150$, Borderline $150\text{--}199$, High $\ge 200$, Severe $\ge 500$ mg/dL |
| **Fasting Blood Glucose**| `mg/dL` | `mmol/L` | FBS, Glucose Fasting | 70–99 mg/dL | **ICMR (2023) / ADA (2024):** Normal $<100$, Impaired $100\text{--}125$, Diabetic $\ge 126$ mg/dL |
| **HbA1c** | `%` | `mmol/mol` | Glycated Hemoglobin, A1c | 4.0–5.6 % | **ICMR (2023) / ADA (2024):** Normal $<5.7\%$, Prediabetes $5.7\text{--}6.4\%$, Diabetes $\ge 6.5\%$ |

---

### 3.2 Allergen Enforcement & Stem Mapping

Allergen exclusions operate as non-negotiable **hard constraints** across all application layers:
- **Composite Normalization:** `"nuts"` or `"Tree nuts & peanuts"` expands automatically to exclude both tree nuts and peanuts (`tree_nuts`, `peanuts`, `nuts`).
- **Deep Ingredient Stems:** Every recipe ingredient line and preparation tip is matched against word stems:
  - `nuts`: `almond`, `badam`, `cashew`, `kaju`, `walnut`, `akhrot`, `pistachio`, `pista`, `peanut`, `groundnut`, `moongphali`, `singdana`, `tree nut`.
  - `dairy`: `milk`, `curd`, `dahi`, `yogurt`, `paneer`, `ghee`, `butter`, `khoa`, `cheese`, `cream`, `whey`.
  - `gluten`: `wheat`, `atta`, `maida`, `suji`, `rava`, `semolina`, `roti`, `chapati`, `bread`.
  - `soy`: `soy`, `soya`, `soybean`, `tofu`, `soya chunks`.
  - `eggs`: `egg`, `anda`, `egg white`, `egg yolk`, `omelette`.
  - `seafood`: `fish`, `machhli`, `prawn`, `shrimp`, `crab`, `mackerel`, `sardine`, `rohu`.
  - `sesame`: `sesame`, `til`, `gingelly`, `tahini`.
  - `mustard`: `mustard`, `sarson`, `rai`.
- **Tip Text Sanitization:** `sanitize_tip_text` rewrites free-text absorption advice (e.g., removing almonds/nuts in LDL and Vitamin D tips).
- **Saved Reports Conflict Detection:** Historic recommendations conflicting with active allergy settings are surfaced with a regeneration trigger.

---

### 3.3 Zero-Tolerance Beef and Pork Elimination

In strict accordance with dietary standards and user guidelines:
- All beef and pork food items, regional dishes (`beef_ularthiyathu`, `pork_bamboo_shoot`), and recipe ingredients are eliminated from the database.
- UI meat selection controls strictly limit non-vegetarian options to `chicken`, `mutton`, `fish`, `seafood`, and `egg`.

---

### 3.4 ICMR-NIN (2020) Energy & Nutrient Equations

Nutritional calculations strictly reflect ICMR-NIN (2020) Dietary Guidelines for Indians:

1. **Basal Metabolic Rate (BMR):**
   - Men (18–29): $\text{BMR} = 15.3 \times \text{Weight (kg)} + 679\text{ kcal/day}$
   - Women (18–29): $\text{BMR} = 14.7 \times \text{Weight (kg)} + 496\text{ kcal/day}$
   - Men (30–59): $\text{BMR} = 11.6 \times \text{Weight (kg)} + 879\text{ kcal/day}$
   - Women (30–59): $\text{BMR} = 8.7 \times \text{Weight (kg)} + 829\text{ kcal/day}$
2. **Physical Activity Level (PAL):**
   - Sedentary (`"none"` / mostly sitting): $\text{PAL} = 1.26$ (Male), $1.30$ (Female).  
     *Reference Indian Man (65 kg) $\rightarrow \mathbf{2,110\text{ kcal/day}}$*
   - Light active (`"walking"`): $\text{PAL} = 1.50$
   - Moderate active (`"cycling"`): $\text{PAL} = 1.62$ (Male $\rightarrow \mathbf{2,710\text{ kcal/day}}$), $1.66$ (Female)
   - Heavy active (`"running"`): $\text{PAL} = 2.00$ (Male $\rightarrow \mathbf{3,350\text{ kcal/day}}$), $2.12$ (Female)
3. **Protein Target:**
   - $\text{Protein RDA} = 0.83\text{ g per kg body weight per day}$ ($65\text{ kg} \rightarrow \mathbf{54.0\text{ g/day}}$).
4. **Sodium and Salt Limit:**
   - Standard Adult Limit: $\le 2,000\text{ mg sodium/day}$ ($\sim 5.0\text{ g salt}$).
   - Hypertensive Adult Limit: $\le 1,500\text{ mg sodium/day}$ ($\sim 3.8\text{ g salt}$).
5. **Transparent Shortfall Reporting:**
   - For deficient nutrients where food intake cannot realistically reach the target under user constraints (e.g. Vitamin D: $42.8\text{--}127\text{ IU}$ actual vs $600\text{ IU}$ target), the shortfall is explicitly quantified and displayed alongside safe clinical guidance for sunlight or physician-directed supplementation.

---

### 3.5 Indian Food Knowledge Base Schema (`foods.json`)
Each food item contains verified nutritional data derived from ICMR-NIN (National Institute of Nutrition, Hyderabad) Indian Food Composition Tables:

```json
{
  "food_id": "moringa_leaves",
  "name": "Drumstick Leaves (Moringa / Murungai)",
  "hindi_name": "Sahjan ke Patte",
  "category": "vegetable",
  "diet_type": ["veg", "vegan"],
  "allergens": [],
  "serving_size": "100g (cooked)",
  "nutrients": {
    "iron_mg": 4.0,
    "calcium_mg": 440.0,
    "folate_mcg": 40.0,
    "vitamin_c_mg": 120.0
  },
  "synergies": [
    "Contains natural Vitamin C which maximizes plant-based non-heme iron absorption."
  ],
  "preparation_tip": "Sauté lightly as a dry sabzi, add to dal, or boil in soups."
}
```

#### Supported Dietary Preferences:
- `veg` (Vegetarian, includes dairy)
- `vegan` (Strict plant-based, no dairy, no eggs)
- `eggetarian` (Vegetarian + eggs)
- `non_veg` (Poultry, fish, seafood, mutton; zero beef/pork)

#### Supported Allergen Filters:
- `dairy` (Milk, paneer, curd, ghee)
- `gluten` (Wheat, maida, barley)
- `nuts` (Combined Tree nuts & Peanuts)
- `soy` (Soybeans, tofu, soy milk)
- `eggs`
- `seafood` (Fish, prawns, shellfish)
- `sesame` (Sesame seeds, til, tahini)
- `mustard` (Mustard seeds, sarson, rai)

---

## 4. API Specification & Endpoints

### 4.1 Base URL: `/api/v1`

#### `POST /api/v1/extract-report`
- **Description:** Upload PDF or text report. Strips PII, runs regex extraction, triggers Gemini JSON fallback if confidence is low, and returns extracted markers.
- **Request:** `multipart/form-data` with `file: UploadFile` or raw JSON `raw_text: str`.
- **Response:**
```json
{
  "session_id": "uuid-string",
  "sanitized_preview": "Patient: [REDACTED] ...",
  "extracted_biomarkers": [
    {
      "biomarker_key": "vitamin_d",
      "display_name": "Vitamin D (25-OH)",
      "detected_value": 14.2,
      "detected_unit": "ng/mL",
      "canonical_value": 14.2,
      "canonical_unit": "ng/mL",
      "report_reference_range": {"low": 30.0, "high": 100.0},
      "extraction_method": "regex",
      "confidence": 0.98
    }
  ],
  "unmatched_text_lines": []
}
```

#### `POST /api/v1/analyze-and-recommend`
- **Description:** Takes verified biomarker values + user profile, executes the deterministic rule engine, filters the Indian food database, injects absorption tips, and synthesizes a grounded summary.
- **Request:**
```json
{
  "user_profile": {
    "age": 24,
    "gender": "female",
    "diet_type": "veg",
    "allergens": ["dairy"]
  },
  "biomarkers": [
    {
      "biomarker_key": "vitamin_d",
      "value": 14.2,
      "unit": "ng/mL",
      "reference_low": 30.0,
      "reference_high": 100.0
    },
    {
      "biomarker_key": "ferritin",
      "value": 9.5,
      "unit": "ng/mL",
      "reference_low": 11.0,
      "reference_high": 307.0
    }
  ]
}
```
- **Response:**
```json
{
  "analysis_id": "uuid-string",
  "timestamp": "2026-11-11T12:00:00Z",
  "status_summary": {
    "total_analyzed": 2,
    "low_count": 2,
    "borderline_count": 0,
    "normal_count": 0,
    "high_count": 0
  },
  "marker_analyses": [
    {
      "biomarker_key": "vitamin_d",
      "display_name": "Vitamin D (25-OH)",
      "value": 14.2,
      "unit": "ng/mL",
      "status": "low",
      "severity": "moderate_deficiency",
      "range_low": 30.0,
      "range_high": 100.0,
      "lab_range_low": 30.0,
      "lab_range_high": 100.0,
      "guideline_threshold": "< 20 ng/mL (Deficient), 20-29.9 ng/mL (Insufficient)",
      "guideline_source": "Endocrine Society Clinical Practice Guidelines",
      "percentage_of_optimal": 47.3,
      "clinical_warning": null
    }
  ],
  "recommendations": [
    {
      "target_biomarker": "ferritin",
      "nutrient_name": "Iron",
      "recommended_foods": [
        {
          "food_id": "moringa_leaves",
          "name": "Drumstick Leaves (Moringa)",
          "hindi_name": "Sahjan ke Patte",
          "serving": "100g cooked",
          "key_nutrient_yield": "4.0 mg Iron (27% RDA)",
          "synergy_tip": "High in natural Vitamin C for enhanced plant-iron absorption."
        }
      ],
      "absorption_dos": [
        "Pair plant iron with Vitamin C sources like amla, lemon, or guava."
      ],
      "absorption_donts": [
        "Avoid tea, coffee, or calcium-rich milk within 1 hour of iron-rich meals (tannins and calcium block iron uptake)."
      ]
    }
  ],
  "grounded_explanation": "Your blood report indicates Vitamin D (14.2 ng/mL) and Ferritin (9.5 ng/mL) are below reference ranges...",
  "requires_physician_consult": true,
  "consult_reasons": ["Ferritin is significantly low (<10 ng/mL). Consult your physician to rule out chronic anemia."]
}
```

#### `POST /api/v1/diet-plan/options`
- **Description:** Uses Google OR-Tools constraint satisfaction solver to generate three distinct single-day meal plans (`familiar`, `nutritious`, `regional`) parameterized with ICMR-NIN (2020) energy, protein, and nutrient targets.
- **Request:**
```json
{
  "profile": {
    "age": 25,
    "gender": "male",
    "height_cm": 170.0,
    "weight_kg": 65.0,
    "activity": "none",
    "diet_type": "veg",
    "allergens": ["nuts"],
    "region": "telangana"
  },
  "markers": [
    {"biomarker_key": "ldl_cholesterol", "status": "high", "target_nutrient_key": "fibre_g"}
  ],
  "picked_foods": []
}
```
- **Response:** Returns `options: PlanDay[]` and calculated `targets: PlanTargets` ($2,110\text{ kcal}$, $54.0\text{ g protein}$).

#### `POST /api/v1/diet-plan/week`
- **Description:** Solves a balanced 7-day regional meal plan enforcing weekly dish limits, non-repetition of mains across consecutive days, starch-stacking constraints, transparent nutrient shortfall accounting, and aggregated purchase-weight shopping list.
- **Response:** Returns `days: PlanDay[]`, `shopping_list: ShoppingItem[]`, and `targets`.

#### `POST /api/v1/diet-plan/swap`
- **Description:** Replaces a specific dish in a meal slot while keeping other meals intact, revalidating strict allergen and dietary exclusions, recalculating nutrient totals and shortfalls.
- **Request:** Includes `day`, `slot` (`breakfast` | `lunch` | `snack` | `dinner`), and `dish_id` to replace.
- **Response:** Returns updated `day: PlanDay`.

#### `POST /api/v1/diet-plan/shopping-list`
- **Description:** Dynamically recalculates the purchase-weight ingredients shopping list from the 7-day meal plan array after any dish swap.
- **Request:** `{"days": [...]}`
- **Response:** `{"shopping_list": [...]}`

#### `POST /api/v1/diet-plan/pdf`
- **Description:** Generates a downloadable A4 PDF of the 7-day meal plan and aisle-categorized shopping list with multilingual localization (English, Hindi, Telugu).

#### `GET /api/v1/history`
- Returns historical reports stored in SQLite/PostgreSQL for longitudinal progress tracking.

#### `POST /api/v1/export-plan-pdf`
- Generates a branded, downloadable A4 PDF of the dietary recommendation plan and preserved biomarker intervals.

---

## 5. Privacy & De-Identification Protocol

To satisfy security criteria and clinical data privacy:
1. **PII Masking:** Before raw text or unparsed PDF snippets are routed to any external API (Gemini), a sanitization pass runs locally via regex to scrub:
   - Patient Names (`Name: [A-Za-z ]+`)
   - Contact Numbers (`(\+91|0)?[6-9]\d{9}`)
   - Email Addresses (`[\w\.-]+@[\w\.-]+\.\w+`)
   - Hospital / Clinic Registration & UHID IDs
2. **Local Storage:** SQLite stores only anonymized analysis sessions keyed by random UUIDs unless explicit local user accounts are created.

---

## 6. Evaluation Framework & Benchmark (For Day 9 & Viva)

### 6.1 Evaluation Dataset
- **Synthetic Report Pool:** 20 generated synthetic PDF blood reports covering:
  - 5 standard single-column reports (e.g., Dr. Lal PathLabs style)
  - 5 multi-column table reports (Metropolis / SRL style)
  - 5 irregular whitespace & varied alias reports
  - 5 noisy reports with edge-case units (`nmol/L`, `g/L`)

### 6.2 Metrics & Ablation Table
We will empirically measure and report:
1. **Biomarker Extraction Precision & Recall:** Target $\ge 95\%$ on canonical 6 markers.
2. **Unit Conversion Accuracy:** 100% adherence on conversion test suite.
3. **Allergen & Diet Safety Rate:** Target **100.0%** (Zero allergen violations across 100 test permutations).
4. **Ablation Comparison:**
   - Method A: Deterministic Regex-only parser.
   - Method B: Hybrid (Regex + Gemini JSON Fallback).
   - *Hypothesis to prove:* Method B maintains >95% accuracy on distorted layouts where Method A drops below 65%.

---

## 7. Directory Structure

```text
NutriLens/
├── SPEC.md                                 # Single Source of Truth
├── README.md                               # Project presentation & setup
├── backend/
│   ├── app/
│   │   ├── main.py                         # FastAPI App initialization & CORS
│   │   ├── config.py                       # Settings & environment variables
│   │   ├── data/
│   │   │   ├── biomarkers.json             # 6 Biomarker ranges, aliases, units
│   │   │   └── foods.json                  # 60+ Indian foods with ICMR nutrients
│   │   ├── models/
│   │   │   ├── schemas.py                  # Pydantic request/response models
│   │   │   └── database.py                 # SQLAlchemy SQLite models
│   │   ├── parsers/
│   │   │   ├── sanitizer.py                # PII Redaction module
│   │   │   ├── pdf_extractor.py            # pdfplumber table & text parsing
│   │   │   ├── regex_matcher.py            # Alias dictionary & regex parser
│   │   │   └── llm_fallback.py             # Gemini GenAI structured fallback
│   │   ├── engine/
│   │   │   ├── allergen_rules.py           # Deep ingredient stems, composite expansion & tip sanitizer
│   │   │   ├── unit_converter.py           # Canonical unit conversions
│   │   │   ├── rule_engine.py              # Status, lab range preservation & guideline threshold rules
│   │   │   ├── recommender.py              # Food ranking, allergen & diet filters
│   │   │   └── explanation_generator.py    # Grounded synthesis
│   │   ├── plan/                           # OR-Tools Constraint Meal Planning Engine
│   │   │   ├── engine.py                   # BMR, PAL, targets, OR-Tools solver, starch penalties, shortfalls
│   │   │   ├── catalog.py                  # Regional recipes loader (North, South, West, East)
│   │   │   └── dishes/                     # Curated regional dish files (Zero beef/pork)
│   │   └── api/
│   │       ├── v1/
│   │       │   ├── router.py               # Combined API routers
│   │       │   ├── extract.py              # Upload & parse endpoints
│   │       │   ├── recommend.py            # Recommendation & analysis
│   │       │   ├── plan.py                 # Meal plan options, 7-day week, swaps, shopping list
│   │       │   └── history.py              # History & PDF export
│   └── tests/
│       ├── test_mentor_regression.py       # Mentor acceptance regression suite (allergens, lab ranges, ICMR targets)
│       ├── test_plan_engine.py             # OR-Tools solver, targets, PAL, starch penalty, shortfalls
│       ├── test_dishes.py                  # Regional dish nutrition & zero beef/pork verification
│       ├── test_unit_converter.py          # Conversion tests
│       ├── test_rule_engine.py             # Deterministic status tests
│       ├── test_recommender.py             # Allergen safety constraint tests
│       └── test_sanitizer.py               # PII masking verification
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── Navbar.tsx
│       │   ├── UploadZone.tsx              # Drag-and-drop PDF upload
│       │   ├── VerificationTable.tsx       # Human-in-the-loop confirmation
│       │   ├── UserProfileForm.tsx         # Diet type, age, sex, allergens
│       │   ├── RangeSliderBar.tsx          # InsideTracker-style visual range
│       │   ├── FoodCard.tsx                # ZOE-style food & synergy card
│       │   ├── HistoryDashboard.tsx        # Longitudinal trends
│       │   └── DisclaimerModal.tsx         # Medical safety guardrail
│       └── services/api.ts                 # Axios / Fetch client
├── evaluation/
│   ├── synthetic_generator.py              # ReportLab synthetic PDF generator
│   ├── benchmark_runner.py                 # Extraction & ablation tester
│   └── ground_truth/                       # 20 ground truth JSON files
└── docs/                                   # Documentation chapters & technical artifacts
    ├── final_report_draft.docx
    ├── poster_A1_layout.pdf
    └── slide_deck.pptx
```

