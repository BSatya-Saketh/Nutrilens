"""Mentor acceptance criteria regression test suite.

Validates the end-to-end fixes requested for:
1. Hard allergen enforcement (specifically tree nuts & peanuts) across food cards,
   tips (LDL & Vitamin D tip paths), recipes, swaps, and shopping lists.
2. Biomarker lab interval preservation and separate guideline thresholds.
3. ICMR-NIN 2020 energy & nutrient targets for sedentary and active profiles.
4. Transparent nutrient accounting and shortfalls reporting (e.g. Vitamin D).
5. Swap re-checking constraints and updating the shopping list.
6. Total removal of beef and pork.
"""
import pytest
from app.engine.allergen_rules import normalize_allergens, sanitize_tip_text, is_dish_allergen_free
from app.engine.recommender import RecommendationEngine
from app.engine.rule_engine import RuleEngine
from app.models.schemas import MarkerInput, UserProfile
from app.plan.engine import Person, targets, eligible, options, week, swap, shopping_list
from app.plan.catalog import catalog
from app.plan.ingredient_names import INGREDIENTS


def test_hard_allergen_tree_nuts_and_peanuts_exclusion():
    """Mentor regression 1: 'Tree nuts & peanuts' must strictly exclude almonds in LDL tips,

    nuts in Vit D tips, food cards, and dishes across the pipeline.
    """
    # 1. Normalization covers both tree nuts and peanuts
    norm = normalize_allergens(["nuts", "Tree nuts & peanuts"])
    assert "nuts" in norm
    assert "tree_nuts" in norm
    assert "peanuts" in norm

    # 2. Tip text sanitization
    # Regression case: LDL tips recommended almonds
    raw_ldl_tip = "Include almonds and walnuts daily to reduce LDL cholesterol and improve HDL."
    clean_ldl_tip = sanitize_tip_text(raw_ldl_tip, norm)
    assert "almond" not in clean_ldl_tip.lower()
    assert "walnut" not in clean_ldl_tip.lower()
    assert "chia" in clean_ldl_tip.lower() or "sunflower" in clean_ldl_tip.lower() or "seeds" in clean_ldl_tip.lower()

    # Regression case: Vitamin D tips recommended nuts
    raw_vitd_tip = "Take vitamin D with healthy fats such as nuts or whole milk to enhance absorption."
    clean_vitd_tip = sanitize_tip_text(raw_vitd_tip, norm)
    assert "nuts" not in clean_vitd_tip.lower()
    assert "healthy fats" in clean_vitd_tip.lower()

    # 3. Dish allergen checking: no dish containing peanuts or tree nuts is eligible
    user = Person(age=25, sex="male", height_cm=170, weight_kg=65, activity="none",
                  diet="veg", allergens=("nuts",))
    eligible_dishes = eligible(user)
    for d in eligible_dishes:
        assert is_dish_allergen_free(d, norm)
        # Deep check: verify no recipe ingredient contains almond, peanut, kaju, etc.
        for line in d["ingredients"]:
            name = line["name"].lower()
            assert not any(stem in name for stem in ("peanut", "groundnut", "almond", "badam", "cashew", "kaju", "pista"))


def test_lab_reported_interval_preserved_and_guidelines_labeled():
    """Mentor regression 2: LDL of 158 mg/dL was extracted with a lab interval of 0-129 mg/dL.

    Keep reported interval intact (0-129). Show clinical guideline threshold (<100 mg/dL)
    separately with citation.
    """
    engine = RuleEngine()
    profile = UserProfile(age=25, gender="male", diet_type="veg", allergens=[])
    marker = MarkerInput(
        biomarker_key="ldl_cholesterol",
        value=158.0,
        unit="mg/dL",
        reference_low=0.0,
        reference_high=129.0,
    )
    res = engine.evaluate_marker(marker, profile)

    # Reported lab interval must remain intact (0 - 129 mg/dL)
    assert res.lab_range_low == 0.0
    assert res.lab_range_high == 129.0
    assert res.range_low == 0.0
    assert res.range_high == 129.0

    # Clinical guideline threshold must be separately provided and labeled
    assert res.guideline_threshold is not None
    assert "< 100" in res.guideline_threshold
    assert res.guideline_source is not None
    assert "LAI" in res.guideline_source or "NCEP" in res.guideline_source

    # Evaluated status reflects clinical borderline/high based on guideline
    assert res.status in ("borderline", "high")


def test_icmr_nin_2020_energy_and_protein_targets():
    """Mentor regression 3: Check QA synthetic profile:

    Age 25, Male, 170 cm, 65 kg, mostly sitting.
    Trace formulas to ICMR-NIN 2020 Reference Indian Sedentary Man (2,110 kcal, 54.0 g protein).
    """
    qa_sedentary = Person(age=25, sex="male", height_cm=170, weight_kg=65, activity="none")
    t_sed = targets(qa_sedentary)

    # ICMR-NIN 2020: BMR = 15.3 * 65 + 679 = 1,673.5 kcal. PAL = 1.26.
    # Energy = 1,673.5 * 1.26 = 2,108.6 kcal -> rounded to 2,109 or 2,110 kcal.
    assert t_sed["energy_kcal"] in (2109, 2110)
    # Protein = 0.83 g/kg * 65 kg = 53.95 g -> 54.0 g / 53.9 g
    assert t_sed["protein_g"] in (53.9, 54.0)
    assert t_sed["pal"] == 1.26
    assert "ICMR-NIN" in t_sed["standards_source"]

    # Active profile: Cycling / Moderate activity
    qa_moderate = Person(age=25, sex="male", height_cm=170, weight_kg=65, activity="cycling")
    t_mod = targets(qa_moderate)
    # PAL = 1.62 -> 1,673.5 * 1.62 = 2,711 kcal
    assert t_mod["energy_kcal"] in (2710, 2711)
    assert t_mod["pal"] == 1.62


def test_transparent_shortfalls_and_regional_meal_plan():
    """Mentor regression 4: Realistic meal planning, manageable portions, and transparent shortfalls

    (e.g., Vitamin D where food alone provides ~42-127 IU against 600 IU target).
    """
    person = Person(age=25, sex="female", height_cm=160, weight_kg=55, activity="walking",
                    diet="veg", region="telangana", low_nutrients=("vitamin_d_iu", "iron_mg"))
    opts = options(person)
    assert len(opts) == 3

    for opt in opts:
        # Vitamin D shortfall should be transparently recorded
        assert "shortfalls" in opt
        if not opt["rda_met"].get("vitamin_d_iu", False):
            vit_d_shortfall = opt["shortfalls"].get("vitamin_d_iu")
            assert vit_d_shortfall is not None
            assert vit_d_shortfall["target"] == 600
            assert "sun" in vit_d_shortfall["note"].lower() or "supplement" in vit_d_shortfall["note"].lower()

        # Workable portions and sensible meals
        assert len(opt["meals"]["lunch"]) <= 5
        assert len(opt["meals"]["dinner"]) <= 5


def test_swap_updates_totals_and_rebuilds_shopping_list():
    """Mentor regression 5: Swapping a dish rechecks allergies, recalculates totals,

    and shopping list is rebuilt from the updated plan.
    """
    person = Person(age=28, sex="female", height_cm=158, weight_kg=54, activity="walking",
                    diet="veg", allergens=("nuts",), region="telangana")
    opts = options(person)
    day = opts[0]

    # Swap one dish in lunch
    lunch_dishes = day["meals"]["lunch"]
    old_dish = lunch_dishes[0]["dish_id"]
    new_day = swap(person, day, "lunch", old_dish)

    assert new_day is not None
    new_lunch_ids = [i["dish_id"] for i in new_day["meals"]["lunch"]]
    assert old_dish not in new_lunch_ids

    # Shopping list rebuilt from the updated days
    old_shop = shopping_list([day])
    new_shop = shopping_list([new_day])
    assert old_shop != new_shop
    # Ensure no nuts in shopping list
    assert not any("almond" in item["name"].lower() or "peanut" in item["name"].lower() for item in new_shop)


def test_beef_and_pork_completely_removed():
    """User instruction: verify all beef and pork dishes, ingredients, and references

    are eliminated from the catalog and codebase.
    """
    all_dish_ids = set(catalog().keys())
    assert "beef_ularthiyathu" not in all_dish_ids
    assert "pork_bamboo_shoot" not in all_dish_ids

    for d_id, dish in catalog().items():
        assert "beef" not in d_id.lower()
        assert "pork" not in d_id.lower()
        assert "beef" not in dish["meat_types"]
        assert "pork" not in dish["meat_types"]
        for ing in dish["ingredients"]:
            assert "beef" not in ing["name"].lower()
            assert "pork" not in ing["name"].lower()

    assert "beef" not in INGREDIENTS
    assert "pork" not in INGREDIENTS


def test_saved_report_allergy_conflict_detection():
    """
    Mentor Requirement:
    'For previously saved reports, preserve the original lab data. If an old recommendation
    conflicts with its saved allergy settings, surface the conflict and provide a safe way to regenerate it.'
    """
    from app.engine.allergen_rules import check_saved_report_allergy_conflicts

    synthetic_saved_analysis = {
        "user_profile": {
            "age": 28,
            "gender": "female",
            "diet_type": "veg",
            "allergens": ["Tree nuts & peanuts"],
        },
        "marker_analyses": [
            {
                "biomarker_key": "serum_ferritin",
                "display_name": "Ferritin",
                "value": 11.2,
                "unit": "ng/mL",
                "status": "low",
                "lab_range_low": 15.0,
                "lab_range_high": 150.0,
            }
        ],
        "recommendations": [
            {
                "target_biomarker": "serum_ferritin",
                "recommended_foods": [
                    {
                        "id": "almonds_badam",
                        "name": "Almonds (Badam)",
                        "allergens": ["nuts"],
                        "preparation_tip": "Soak 5-6 almonds overnight.",
                    },
                    {
                        "id": "palak_spinach",
                        "name": "Spinach (Palak)",
                        "allergens": [],
                        "preparation_tip": "Cook with lemon juice.",
                    }
                ]
            }
        ],
        "diet_plan": None
    }

    conflicts_info = check_saved_report_allergy_conflicts(synthetic_saved_analysis)

    # 1. Surface the conflict
    assert conflicts_info["can_regenerate"] is True
    assert len(conflicts_info["allergy_conflicts"]) > 0
    assert any("Almonds" in c for c in conflicts_info["allergy_conflicts"])

    # 2. Original lab data preserved
    assert synthetic_saved_analysis["marker_analyses"][0]["value"] == 11.2
    assert synthetic_saved_analysis["marker_analyses"][0]["lab_range_low"] == 15.0

    # 3. Clean profile with no allergy conflicts
    clean_analysis = {
        "user_profile": {"allergens": ["dairy"]},
        "recommendations": [
            {
                "recommended_foods": [
                    {"id": "palak_spinach", "name": "Spinach", "allergens": []}
                ]
            }
        ]
    }
    clean_info = check_saved_report_allergy_conflicts(clean_analysis)
    assert clean_info["can_regenerate"] is False
    assert len(clean_info["allergy_conflicts"]) == 0
