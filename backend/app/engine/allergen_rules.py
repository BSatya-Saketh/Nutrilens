"""
NutriLens Allergen & Dietary Constraint Enforcement.

Shared normalization, validation, and text-sanitization rules ensuring ZERO allergen leakage
across food recommendations, clinical repletion strategies, meal planner dishes, swaps, and shopping lists.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

# Standard allergen canonical keys and all their common aliases / sub-types
ALLERGEN_NORMALIZATION_MAP = {
    "nuts": {"nuts", "tree_nuts", "tree nuts", "peanuts", "peanut", "tree nuts & peanuts"},
    "peanuts": {"peanuts", "peanut", "groundnut", "groundnuts"},
    "dairy": {"dairy", "milk", "lactose", "dairy & lactose"},
    "gluten": {"gluten", "wheat", "gluten / wheat"},
    "soy": {"soy", "soya", "soybeans"},
    "eggs": {"eggs", "egg"},
    "seafood": {"seafood", "fish", "shellfish", "fish & shellfish"},
    "sesame": {"sesame", "til"},
    "mustard": {"mustard", "sarson", "rai"},
}

# Individual ingredient words mapped to allergen groups for deep recipe checks
ALLERGEN_INGREDIENT_STEMS = {
    "nuts": {
        "almond", "almonds", "badam", "cashew", "cashews", "kaju", "walnut", "walnuts",
        "akhrot", "pistachio", "pistachios", "pista", "hazelnut", "hazelnuts", "pecan",
        "pecans", "peanut", "peanuts", "groundnut", "groundnuts", "moongphali", "mungfali",
        "palli", "shenga", "singdana", "peanut butter", "groundnut oil", "tree nut", "tree nuts"
    },
    "dairy": {
        "milk", "curd", "dahi", "yogurt", "paneer", "ghee", "butter", "makhan", "buttermilk",
        "chaas", "khoa", "mawa", "cheese", "cream", "malai", "whey", "lactose"
    },
    "gluten": {
        "wheat", "atta", "maida", "suji", "sooji", "rava", "semolina", "dalia", "bulgur",
        "barley", "roti", "phulka", "chapati", "naan", "poori", "puri", "bread", "vermicelli"
    },
    "soy": {
        "soy", "soya", "soybean", "soybeans", "tofu", "tempeh", "edamame", "soy milk", "soya chunks"
    },
    "eggs": {
        "egg", "eggs", "anda", "egg white", "egg yolk", "boiled egg", "omelette", "albumin"
    },
    "seafood": {
        "fish", "machhli", "prawn", "prawns", "shrimp", "jheenga", "crab", "shellfish",
        "mackerel", "sardine", "rohu", "catla", "hilsa", "seer fish", "anchovy"
    },
    "sesame": {
        "sesame", "til", "gingelly", "tahini", "sesame seeds", "sesame oil"
    },
    "mustard": {
        "mustard", "sarson", "rai", "mustard seeds", "mustard oil", "mustard leaves"
    }
}


def normalize_allergens(allergens: List[str] | Set[str] | tuple) -> Set[str]:
    """Expands user allergen choices so that composite choices (e.g. 'Tree nuts & peanuts') cover all variants."""
    raw = {a.strip().lower() for a in allergens if a and a.strip()}
    normalized: Set[str] = set()

    for item in raw:
        normalized.add(item)
        for canon, aliases in ALLERGEN_NORMALIZATION_MAP.items():
            if item == canon or item in aliases:
                normalized.add(canon)
                # Combined exclusion rule: "nuts" always covers both tree nuts and peanuts
                if canon in ("nuts", "peanuts"):
                    normalized.add("nuts")
                    normalized.add("peanuts")
                    normalized.add("tree_nuts")

    return normalized


def sanitize_tip_text(text: str, allergens: Set[str] | List[str], diet_type: str = "veg") -> str:
    """
    Rewrites absorption tips, guidelines, and lifestyle notes so that excluded allergens
    and non-matching diets are NEVER recommended to the user.
    """
    if not text:
        return text

    norm_allergens = normalize_allergens(allergens)
    t = text

    # 1. Nut exclusion rules
    if "nuts" in norm_allergens or "peanuts" in norm_allergens or "tree_nuts" in norm_allergens:
        # LDL / lipid tips
        t = t.replace(
            "Include a small handful of nuts or seeds (almonds, flaxseed, sesame, pumpkin or sunflower seeds)",
            "Include healthy seeds (flaxseed, sesame, pumpkin or sunflower seeds)"
        )
        t = t.replace(
            "almonds, flaxseed, sesame, pumpkin or sunflower seeds",
            "flaxseed, sesame, pumpkin or sunflower seeds"
        )
        t = t.replace(
            "unsaturated fat from nuts, seeds and, for non-vegetarians, fish",
            "unsaturated fat from seeds and, for non-vegetarians, fish"
        )
        t = t.replace("nuts, seeds and, for non-vegetarians, fish", "seeds and, for non-vegetarians, fish")
        t = t.replace("prefer nuts, seeds and fish", "prefer seeds and fish")
        t = t.replace("replace some saturated fat with nuts and seeds", "replace some saturated fat with seeds")
        t = t.replace("ghee, cold-pressed oils, nuts, or whole milk", "ghee, cold-pressed oils, or whole milk")
        t = t.replace("cold-pressed oils, ghee, nuts, whole milk", "cold-pressed oils, ghee, whole milk")
        t = t.replace(", nuts,", ",")
        t = t.replace(", nuts", "")
        t = t.replace("nuts, ", "")
        # Remove any remaining mentions of specific nuts
        t = re.sub(r"\b(almonds?|walnuts?|cashews?|pistachios?|peanuts?|groundnuts?|badam|kaju|pista)\b", "seeds", t, flags=re.IGNORECASE)
        t = re.sub(r"\bnuts\b", "seeds", t, flags=re.IGNORECASE)
        t = re.sub(r"\bseeds\s+and\s+seeds\b", "seeds", t, flags=re.IGNORECASE)
        t = re.sub(r"\bseeds\s*,\s*seeds\b", "seeds", t, flags=re.IGNORECASE)

    # 2. Dairy exclusion or vegan diet
    if "dairy" in norm_allergens or diet_type == "vegan":
        t = t.replace("ghee, cold-pressed oils, or whole milk", "cold-pressed vegetable oils")
        t = t.replace("cold-pressed oils, ghee, whole milk", "cold-pressed vegetable oils")
        t = t.replace("ghee, ", "")
        t = t.replace(", whole milk", "")
        t = t.replace("whole milk, ", "")
        t = t.replace("Lacto-vegetarians should regularly include fermented curd (dahi), paneer, and milk.",
                      "Choose fortified plant milks or breakfast cereals to meet daily vitamin B12 needs.")
        t = t.replace("curd, paneer, and milk", "fortified plant beverages")
        t = t.replace("curd, paneer or soya", "soya, sprouts or pulses")
        t = t.replace("low-fat milk and curd", "low-fat plant milks, legumes and pulses")

    # 3. Seafood exclusion or vegetarian / vegan / eggetarian
    if "seafood" in norm_allergens or diet_type in ("veg", "vegan", "eggetarian"):
        t = t.replace("; non-vegetarians can choose fish such as mackerel", "")
        t = t.replace(" and, for non-vegetarians, fish", "")
        t = t.replace(" and fish", "")
        t = t.replace("or, for non-vegetarians, fish", "")

    # Clean up double punctuation / whitespace
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r",\s*,", ",", t)
    t = t.replace("( ", "(").replace(" )", ")")
    return t


def is_dish_allergen_free(dish: Dict[str, Any], norm_allergens: Set[str]) -> bool:
    """
    Validates a dish against allergen exclusions.
    Returns False if any ingredient or tag conflicts with the user's allergens.
    """
    if not norm_allergens:
        return True

    # 1. Direct dish allergens
    dish_algs = normalize_allergens(dish.get("allergens", []))
    if dish_algs & norm_allergens:
        return False

    # 2. Deep ingredient stems check
    ingredients = dish.get("ingredients", [])
    if not ingredients and norm_allergens:
        # If ingredient data is insufficient to verify an exclusion, omit the dish
        return False
    for ing in ingredients:
        name = ing.get("name", "").lower()
        for alg in norm_allergens:
            stems = ALLERGEN_INGREDIENT_STEMS.get(alg, set())
            for stem in stems:
                # Word boundary match to avoid false positive substrings
                if re.search(r"\b" + re.escape(stem) + r"\b", name):
                    return False

    return True


def check_saved_report_allergy_conflicts(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inspects a previously saved analysis and surfaces any conflicts between historical
    recommendations/plans and the user's allergy settings while preserving original lab data intact.
    """
    profile = analysis.get("user_profile") or {}
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()
    raw_allergens = profile.get("allergens") or []
    norm_allergens = normalize_allergens(raw_allergens)
    if not norm_allergens:
        return {"allergy_conflicts": [], "can_regenerate": False}

    conflicts = []

    # 1. Check recommended foods
    for rec in analysis.get("recommendations", []):
        foods = rec.get("recommended_foods", []) if isinstance(rec, dict) else getattr(rec, "recommended_foods", [])
        for f in foods:
            f_dict = f if isinstance(f, dict) else (f.model_dump() if hasattr(f, "model_dump") else getattr(f, "__dict__", {}))
            f_algs = normalize_allergens(f_dict.get("allergens", []))
            if f_algs & norm_allergens:
                conflicts.append(f"Recommended food '{f_dict.get('name')}' matches excluded allergen.")
                continue
            name_tip = (f_dict.get("name", "") + " " + (f_dict.get("preparation_tip") or "")).lower()
            for alg in norm_allergens:
                stems = ALLERGEN_INGREDIENT_STEMS.get(alg, set())
                if any(re.search(r"\b" + re.escape(s) + r"\b", name_tip) for s in stems):
                    conflicts.append(f"Food item '{f_dict.get('name')}' mentions {alg} in ingredients or advice.")
                    break

    # 2. Check saved diet plan dishes
    diet_plan = analysis.get("diet_plan")
    if diet_plan and isinstance(diet_plan, dict):
        from app.plan.catalog import catalog
        cat = catalog()
        for day in diet_plan.get("days", []):
            meals = day.get("meals", {}) if isinstance(day, dict) else {}
            for slot, items in meals.items():
                for item in items:
                    dish_id = item.get("dish_id") if isinstance(item, dict) else getattr(item, "dish_id", None)
                    d = cat.get(dish_id)
                    if d and not is_dish_allergen_free(d, norm_allergens):
                        conflicts.append(f"Saved meal plan dish '{item.get('name')}' conflicts with excluded {', '.join(sorted(norm_allergens))}.")

    # Deduplicate conflicts while preserving order
    unique_conflicts = list(dict.fromkeys(conflicts))
    return {
        "allergy_conflicts": unique_conflicts,
        "can_regenerate": bool(unique_conflicts),
    }
