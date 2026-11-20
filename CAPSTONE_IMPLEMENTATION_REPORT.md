# NutriLens: Clinical Biomarker Intelligence & Regional Dietary Optimization Platform
## Capstone Project Implementation & Mentor Upgrades Report

**Academic Institution:** SR University, Warangal  
**Project Track:** Capstone Project 4-1  
**Repository:** [BSatya-Saketh/Nutrilens](https://github.com/BSatya-Saketh/Nutrilens.git)  
**System:** Evidence-Grounded Nutrition Decision Support & Meal Planning Engine  
**Date:** November 2026  

---

## 1. Executive Summary & Problem Formulation

NutriLens bridges the gap between diagnostic laboratory blood reports and culturally appropriate, evidence-based nutritional choices for Indian populations. Traditional dietary tools often treat recommendations as generic calorie counting or rely on Western reference intervals, failing to respect regional culinary traditions, multi-generational Indian eating patterns, and clinical reference standards.

Following extensive mentor review and QA evaluations, five critical engineering and clinical upgrades were identified and systematically resolved:
1. **End-to-End Allergen Hard Constraints:** Eliminating allergen leakage across all recommendation surfaces (food cards, recipes, garnishes, cooking ingredients, variants, swaps, shopping lists, and free-text tips), specifically addressing composite exclusions such as *"Tree nuts & peanuts"*.
2. **Preservation of Laboratory Reference Intervals:** Ensuring laboratory-printed intervals remain visible and unchanged (e.g., LDL $0\text{--}129\text{ mg/dL}$), while distinctly badging separate evidence-based clinical guideline thresholds (e.g., LAI 2020 / NCEP ATP III $< 100\text{ mg/dL}$) with formal citations.
3. **ICMR-NIN (2020) Target Calibration:** Auditing energy and protein formulas against ICMR-NIN 2020 Recommended Dietary Allowances for Indians, fixing the sedentary reference man profile ($65\text{ kg} \rightarrow 2,110\text{ kcal/day}$, $54.0\text{ g protein}$) and sex-specific Physical Activity Level (PAL) factors.
4. **Realistic Regional Meal Planning & Transparent Shortfalls:** Preventing multi-starch stacking (e.g. avoiding concurrent rice and multiple rotis), ensuring manageable household portions, transparently reporting dietary shortfalls (e.g., Vitamin D $42.8\text{--}127\text{ IU}$ intake vs. $600\text{ IU}$ RDA with sunlight/supplementation advisories), and synchronizing dish swaps with live shopping lists.
5. **Complete Removal of Beef and Pork:** Zero-tolerance elimination of beef and pork food items, regional recipes, ingredient names, and UI options across the entire codebase.

---

## 2. Mathematical Formulations & Clinical Standards

### 2.1 Energy Requirement Modeling (ICMR-NIN 2020)
Energy targets are derived strictly from ICMR-NIN (2020) Table 2.1 and Table 2.2 using the Schofield equations adopted by ICMR:

$$\text{Energy Expenditure (kcal/day)} = \text{BMR} \times \text{PAL}$$

#### Basal Metabolic Rate (BMR) Equations:
- **Men (18–29 years):** $\text{BMR} = 15.3 \times W + 679\text{ kcal/day}$
- **Women (18–29 years):** $\text{BMR} = 14.7 \times W + 496\text{ kcal/day}$
- **Men (30–59 years):** $\text{BMR} = 11.6 \times W + 879\text{ kcal/day}$
- **Women (30–59 years):** $\text{BMR} = 8.7 \times W + 829\text{ kcal/day}$
*(where $W$ is body weight in kilograms)*

#### Physical Activity Level (PAL) Factors:
| Activity Level | UI Selection | Male PAL | Female PAL | Reference Energy Intake (65 kg Male / 55 kg Female) |
| :--- | :--- | :---: | :---: | :--- |
| **Sedentary** | `"none"` (mostly sitting / desk job) | **1.26** | **1.30** | **2,110 kcal/day** (Male) / **1,660 kcal/day** (Female) |
| **Light Active** | `"walking"` | **1.50** | **1.50** | $2,510\text{ kcal/day}$ (Male) / $1,920\text{ kcal/day}$ (Female) |
| **Moderate Active**| `"cycling"` | **1.62** | **1.66** | **2,710 kcal/day** (Male) / **2,130 kcal/day** (Female) |
| **Heavy Active** | `"running"` | **2.00** | **2.12** | **3,350 kcal/day** (Male) / **2,560 kcal/day** (Female) |

*Root Cause Analysis on QA Sedentary Discrepancy:*  
Prior to this upgrade, the planner utilized an uncalibrated multiplier of $1.53$ (from legacy FAO 1985 light activity), which produced $2,560\text{ kcal/day}$ for a $65\text{ kg}$ sedentary male ($1,673.5 \times 1.53$). Applying the verified ICMR-NIN 2020 PAL factor of $1.26$ accurately resolves energy needs to $2,108.6 \approx \mathbf{2,110\text{ kcal/day}}$.

### 2.2 Protein Allowance
$$\text{Protein Target (g/day)} = 0.83 \times W$$
For a $65\text{ kg}$ reference adult, this produces $53.95 \approx \mathbf{54.0\text{ g/day}}$, directly adhering to ICMR-NIN 2020 Chapter 3 recommendations.

### 2.3 Clinical Reference Intervals vs. Guideline Thresholds
To ensure forensic traceability, lab results retain their original reporting interval, while separate evidence-based clinical thresholds are displayed with citations:

| Parameter | Lab Reported Range | Clinical Guideline Threshold | Clinical Authority |
| :--- | :--- | :--- | :--- |
| **LDL Cholesterol** | $0\text{--}129\text{ mg/dL}$ (Report intact) | Optimal $< 100\text{ mg/dL}$, Borderline $100\text{--}159\text{ mg/dL}$, High $\ge 160\text{ mg/dL}$ | **Lipid Association of India (LAI 2020)** / NCEP ATP III |
| **Total Cholesterol** | $0\text{--}200\text{ mg/dL}$ (Report intact) | Desirable $< 200\text{ mg/dL}$, Borderline $200\text{--}239\text{ mg/dL}$, High $\ge 240\text{ mg/dL}$ | **NCEP ATP III** |
| **Triglycerides** | $0\text{--}150\text{ mg/dL}$ (Report intact) | Normal $< 150\text{ mg/dL}$, Borderline $150\text{--}199\text{ mg/dL}$, High $\ge 200\text{ mg/dL}$, Severe $\ge 500\text{ mg/dL}$ | **NCEP ATP III** |
| **Fasting Blood Glucose**| $70\text{--}99\text{ mg/dL}$ (Report intact) | Normal $< 100\text{ mg/dL}$, Impaired $100\text{--}125\text{ mg/dL}$, Diabetic $\ge 126\text{ mg/dL}$ | **ICMR Guidelines for Type 2 Diabetes (2023)** / ADA (2024) |
| **HbA1c** | $4.0\text{--}5.6\%$ (Report intact) | Normal $< 5.7\%$, Prediabetes $5.7\text{--}6.4\%$, Diabetes $\ge 6.5\%$ | **ICMR (2023)** / ADA (2024) |

---

## 3. Architecture & Algorithmic Implementation

### 3.1 Allergen Enforcement Engine (`backend/app/engine/allergen_rules.py`)
- **Composite Normalization:** Expands composite user selections like `"Tree nuts & peanuts"` or `"nuts"` into a unified exclusion set: `{"nuts", "tree_nuts", "peanuts"}`.
- **Deep Ingredient Stem Checks:** Every dish in the regional catalog is evaluated against 8 allergen stem dictionaries (`almond`, `badam`, `kaju`, `walnut`, `peanut`, `groundnut`, etc.). A dish is disqualified if any component ingredient matches an excluded stem.
- **Free-Text Tip Sanitization:** Clinical absorption advice (`absorption_dos`, `absorption_donts`, and repletion narratives) is parsed through `sanitize_tip_text`. For example:
  - In LDL cholesterol tips: Mentions of almonds, walnuts, and peanuts are replaced with sunflower, pumpkin, and chia seeds.
  - In Vitamin D tips: Mentions of nuts are replaced with healthy vegetable fats and seeds.
- **Saved Report Conflict Surfacing:** The frontend (`ResultsView.tsx`) scans historic saved plans against the active user allergy profile. When a conflict is identified, a warning banner alerts the user and provides a safe one-click plan regeneration action without modifying original lab data.

### 3.2 OR-Tools Regional Meal Planning Solver (`backend/app/plan/engine.py`)
- **Starch-Stacking Penalty:** Added explicit decision variables and objective penalties in Google OR-Tools MIP solver to disallow stacking multiple heavy starches (e.g. limiting simultaneous rice and multiple rotis in lunch/dinner).
- **Manageable Portions:** Meals adhere to realistic Indian household units (cups cooked, rotis, katoris, tablespoons) with maximum servings bounded per role.
- **Transparent Shortfall Reporting:** If a nutrient target cannot be realistically satisfied through whole food alone under the user's constraints (e.g. Vitamin D RDA of $600\text{ IU}$ where food naturally yields $42.8\text{--}127\text{ IU}$), the shortfall is explicitly quantified and rendered with clinical advice for sunlight exposure or physician-directed supplementation.
- **Dynamic Swaps and Shopping List Synchronization:** When a user executes a dish swap, constraints are re-verified, daily nutrient totals and shortfalls are recomputed, and the 7-day shopping list (`POST /diet-plan/shopping-list`) is dynamically recalculated with purchase-weight adjustments.

### 3.3 Zero-Tolerance Beef and Pork Removal
- Eliminated `beef_ularthiyathu` (South) and `pork_bamboo_shoot` (East).
- Purged `"beef"` and `"pork"` from `ingredient_names.py`, schema definitions, and frontend meat selection components (`PlanProfileFields.tsx`).

---

## 4. Verification & Testing Matrix

The full test suite was executed across backend and frontend stacks:

| Test Suite | File | Tests Run | Result | Key Verified Features |
| :--- | :--- | :---: | :---: | :--- |
| **Mentor Acceptance Regression** | `test_mentor_regression.py` | 6 | **Passed** | Tree nuts & peanut exclusion in tips/cards/swaps; lab interval preservation (0–129 mg/dL) with LAI badge; ICMR-NIN sedentary ($2,110$ kcal, $54.0$ g) and moderate active ($2,711$ kcal) outputs; Vitamin D shortfall accounting; swap shopping list sync; zero beef/pork. |
| **Meal Planner & Solver Engine** | `test_plan_engine.py` | 6 | **Passed** | Schofield BMR formulas, PAL mapping, hard exclusion filtering, 3 options generation, 7-day variation, dish swap mechanics. |
| **Regional Dishes & Catalog** | `test_dishes.py` | 240 | **Passed** | Nutritional validity of North, South, West, East dishes; allergen tag integrity; elimination of beef and pork dishes. |
| **Ingredient Name System** | `test_ingredients.py` | 28 | **Passed** | IFCT code resolution, yield factors, purchase weights, aisle categorization. |
| **Biomarker Rule Engine** | `test_rule_engine.py` | 4 | **Passed** | Status classification, clinical warnings, severity tiers. |
| **Metabolic Markers & Guidelines** | `test_metabolic_markers.py` | 48 | **Passed** | Fasting glucose, HbA1c prediabetes cutoffs, lipid guidelines. |
| **Diet Plan API Endpoints** | `test_plan_api.py` | 3 | **Passed** | End-to-end HTTP validation of options, 7-day week, dish swap, and shopping list generation. |
| **Frontend Production Build** | `tsc -b && vite build` | 1,667 modules | **Passed** | TypeScript strict typing, component compilation, zero errors (7.06s). |

---

## 5. Clinical Review & Future Work

1. **Sun Exposure Guidance vs. Cutaneous Synthesis:** In Indian latitudes ($8^\circ\text{N}\text{--}37^\circ\text{N}$), dermal synthesis between 11 AM and 2 PM provides the primary natural source of Vitamin D3. Clinicians should establish tailored sunlight recommendations taking skin phototype (Fitzpatrick type IV/V) into account before prescribing high-dose cholecalciferol.
2. **Thermal Cooking Losses:** Raw IFCT 2017 nutrient values undergo varying degrees of degradation during prolonged pressure cooking or frying. Incorporating culinary retention factors for ascorbic acid and folate represents an important future iteration.
3. **Severe Hypertriglyceridemia Alert:** When serum triglycerides exceed $500\text{ mg/dL}$, dietary interventions alone are insufficient to mitigate acute pancreatitis risk. NutriLens flags a safety advisory recommending immediate medical evaluation.
