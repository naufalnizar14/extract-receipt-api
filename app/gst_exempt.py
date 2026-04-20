"""
GST-free items under Australian law.
Source: A New Tax System (Goods and Services Tax) Act 1999
  - Division 38 (GST-free supplies)
  - Division 40 (Input-taxed supplies)

Each entry has:
  keywords   — matched against line item description (case-insensitive)
  categories — matched against item_category slug from compliance taxonomy
  reason     — ATO division / reason for exemption
"""

from __future__ import annotations

GST_FREE_RULES: list[dict] = [

    # -------------------------------------------------------------------------
    # BASIC FOOD — Division 38-2
    # GST-free: unprepared/unprocessed staple foods
    # Taxable: hot food, confectionery, soft drinks, snack foods, alcohol
    # -------------------------------------------------------------------------

    # Bread & cereals
    {"keywords": ["bread", "bread roll", "loaf", "pita", "wrap", "tortilla", "crumpet",
                  "rice cake", "rye", "sourdough", "baguette", "ciabatta"],
     "categories": ["fresh_food_market"],
     "reason": "Basic food — Division 38-2"},

    {"keywords": ["rice", "pasta", "noodle", "flour", "oats", "muesli", "cereal",
                  "grain", "wheat", "barley", "quinoa", "couscous", "semolina"],
     "categories": ["fresh_food_market"],
     "reason": "Basic food — Division 38-2"},

    # Dairy
    {"keywords": ["milk", "full cream milk", "skim milk", "soy milk", "almond milk",
                  "oat milk", "lactose free milk", "powdered milk", "evaporated milk",
                  "condensed milk", "cream", "sour cream", "butter", "margarine",
                  "cheese", "cheddar", "mozzarella", "cottage cheese", "ricotta",
                  "parmesan", "brie", "feta", "gouda", "yoghurt", "yogurt"],
     "categories": ["fresh_food_market", "convenience_store"],
     "reason": "Basic food — Division 38-2"},

    # Eggs
    {"keywords": ["egg", "eggs", "dozen eggs", "free range egg", "cage egg"],
     "categories": ["fresh_food_market", "convenience_store"],
     "reason": "Basic food — Division 38-2"},

    # Meat & seafood (uncooked/unprocessed)
    {"keywords": ["beef", "chicken breast", "chicken thigh", "chicken fillet",
                  "lamb", "pork", "veal", "turkey", "mince", "steak", "chop",
                  "sausage", "bacon", "ham", "deli meat", "salami", "prosciutto",
                  "salmon", "tuna", "cod", "barramundi", "whiting", "prawns",
                  "shrimp", "crab", "lobster", "oyster", "mussel", "squid",
                  "fish fillet", "fish steak", "seafood"],
     "categories": ["fresh_food_market", "meat_deli"],
     "reason": "Basic food — Division 38-2"},

    # Fruit & vegetables (fresh, frozen, dried, canned)
    {"keywords": ["apple", "banana", "orange", "mango", "grape", "strawberry",
                  "blueberry", "raspberry", "watermelon", "pineapple", "pear",
                  "peach", "plum", "cherry", "kiwi", "avocado", "lemon", "lime",
                  "grapefruit", "melon", "papaya", "passionfruit", "fig", "date",
                  "dried fruit", "frozen fruit", "canned fruit",
                  "tomato", "potato", "carrot", "broccoli", "cauliflower",
                  "spinach", "lettuce", "cucumber", "capsicum", "onion", "garlic",
                  "mushroom", "celery", "zucchini", "pumpkin", "sweet potato",
                  "corn", "peas", "beans", "asparagus", "eggplant", "beetroot",
                  "cabbage", "kale", "silverbeet", "leek", "spring onion",
                  "frozen vegetables", "frozen veg", "canned vegetables",
                  "salad mix", "stir fry mix"],
     "categories": ["fresh_food_market", "convenience_store"],
     "reason": "Basic food — Division 38-2"},

    # Fruit juice (100% fruit only)
    {"keywords": ["100% fruit juice", "pure fruit juice", "orange juice fresh",
                  "apple juice fresh", "freshly squeezed juice"],
     "categories": ["fresh_food_market"],
     "reason": "Basic food — Division 38-2"},

    # Cooking ingredients
    {"keywords": ["cooking oil", "olive oil", "vegetable oil", "canola oil",
                  "sunflower oil", "coconut oil", "sugar", "raw sugar", "brown sugar",
                  "icing sugar", "honey", "maple syrup", "salt", "pepper",
                  "vinegar", "soy sauce", "fish sauce", "tomato paste",
                  "canned tomato", "baking powder", "baking soda", "yeast",
                  "vanilla extract", "cocoa powder", "cornflour", "breadcrumbs"],
     "categories": ["fresh_food_market"],
     "reason": "Basic food — Division 38-2"},

    # Tea, coffee (unprocessed/ground)
    {"keywords": ["tea bags", "loose leaf tea", "green tea", "herbal tea",
                  "coffee beans", "ground coffee", "instant coffee", "espresso beans"],
     "categories": ["fresh_food_market", "convenience_store"],
     "reason": "Basic food — Division 38-2"},

    # Baby food & infant formula
    {"keywords": ["baby food", "infant formula", "baby formula", "baby cereal",
                  "baby puree", "toddler formula", "baby milk"],
     "categories": ["fresh_food_market", "pharmacy", "convenience_store"],
     "reason": "Basic food — Division 38-2"},

    # Unflavoured water
    {"keywords": ["still water", "sparkling water", "mineral water", "spring water",
                  "plain water", "unflavoured water"],
     "categories": ["fresh_food_market", "convenience_store"],
     "reason": "Basic food — Division 38-2"},

    # -------------------------------------------------------------------------
    # HEALTH & MEDICAL — Division 38-7
    # -------------------------------------------------------------------------

    {"keywords": ["doctor", "gp visit", "general practitioner", "specialist",
                  "medical consultation", "medical appointment", "physician",
                  "bulk bill", "medicare", "hospital", "emergency", "surgery",
                  "pathology", "blood test", "x-ray", "mri", "ct scan", "ultrasound",
                  "radiology", "imaging", "ambulance"],
     "categories": ["medical_consultations", "pathology_imaging", "occupational_health"],
     "reason": "Medical services — Division 38-7"},

    {"keywords": ["prescription", "prescribed medication", "pbs", "pharmaceutical",
                  "compounded medication"],
     "categories": ["pharmacy"],
     "reason": "Prescription medicines — Division 38-7"},

    {"keywords": ["dental", "dentist", "tooth extraction", "filling", "root canal",
                  "orthodontic", "braces"],
     "categories": ["dental_services"],
     "reason": "Dental services — Division 38-7"},

    {"keywords": ["optometrist", "eye test", "vision test", "ophthalmologist"],
     "categories": ["optical_services"],
     "reason": "Optical services — Division 38-7"},

    {"keywords": ["physiotherapy", "physio", "chiropractic", "osteopath",
                  "occupational therapy", "speech therapy", "audiology",
                  "podiatry", "dietitian", "psychology", "psychologist",
                  "counselling", "mental health"],
     "categories": ["physiotherapy", "mental_health_services", "occupational_health"],
     "reason": "Allied health — Division 38-7"},

    {"keywords": ["hearing aid", "prosthetic", "wheelchair", "crutches",
                  "orthopaedic", "medical device", "medical equipment",
                  "blood glucose monitor", "insulin", "epipen", "nebuliser"],
     "categories": ["pharmacy", "medical_consultations"],
     "reason": "Medical aids — Division 38-7"},

    # -------------------------------------------------------------------------
    # EDUCATION — Division 38-85
    # -------------------------------------------------------------------------

    {"keywords": ["school fees", "tuition", "tafe", "university fee", "course fee",
                  "enrolment fee", "student fee", "vet course", "training course",
                  "accredited course", "certificate", "diploma", "degree"],
     "categories": ["university_fees", "online_courses", "trade_certifications",
                    "professional_development", "seminars_conferences"],
     "reason": "Education — Division 38-85"},

    # -------------------------------------------------------------------------
    # CHILDCARE — Division 38-145
    # -------------------------------------------------------------------------

    {"keywords": ["childcare", "child care", "daycare", "day care", "kindergarten",
                  "preschool", "before school care", "after school care", "oshc",
                  "vacation care"],
     "categories": [],
     "reason": "Childcare — Division 38-145"},

    # -------------------------------------------------------------------------
    # WATER & SEWERAGE — Division 38-285/290
    # -------------------------------------------------------------------------

    {"keywords": ["water rates", "water usage", "sewerage", "drainage charges",
                  "council water", "water supply"],
     "categories": ["water_rates"],
     "reason": "Water & sewerage — Division 38-285"},

    # -------------------------------------------------------------------------
    # GOVERNMENT FEES & CHARGES — Division 81
    # -------------------------------------------------------------------------

    {"keywords": ["council rates", "court fee", "tribunal fee", "government fee",
                  "rego", "vehicle registration", "drivers licence",
                  "passport fee", "visa application fee", "birth certificate",
                  "marriage certificate", "land tax", "stamp duty"],
     "categories": ["council_rates", "court_fees", "government_fees_charges",
                    "licenses_permits", "motor_registration"],
     "reason": "Government fees — Division 81"},

    # -------------------------------------------------------------------------
    # EXPORTS — Division 38-185
    # -------------------------------------------------------------------------

    {"keywords": ["export", "exported goods", "international freight", "overseas delivery"],
     "categories": [],
     "reason": "Exports — Division 38-185"},

    # -------------------------------------------------------------------------
    # FINANCIAL SERVICES (Input-taxed) — Division 40
    # These are NOT GST-free but are input-taxed (no GST charged or claimed)
    # -------------------------------------------------------------------------

    {"keywords": ["bank fee", "account keeping fee", "overdraft fee", "loan fee",
                  "interest charge", "credit card annual fee", "mortgage",
                  "insurance premium", "life insurance", "income protection",
                  "workers compensation premium"],
     "categories": ["bank_fees_charges", "business_insurance", "professional_indemnity",
                    "public_liability", "workers_compensation", "vehicle_insurance"],
     "reason": "Input-taxed financial services — Division 40"},

    # -------------------------------------------------------------------------
    # RESIDENTIAL RENT (Input-taxed) — Division 40-35
    # -------------------------------------------------------------------------

    {"keywords": ["residential rent", "rent payment", "lease payment residential",
                  "accommodation bond"],
     "categories": [],
     "reason": "Input-taxed residential rent — Division 40-35"},

    # -------------------------------------------------------------------------
    # PRECIOUS METALS — Division 38-385
    # -------------------------------------------------------------------------

    {"keywords": ["gold bullion", "silver bullion", "precious metal", "gold bar",
                  "silver bar", "platinum"],
     "categories": [],
     "reason": "Precious metals — Division 38-385"},

    # -------------------------------------------------------------------------
    # FINES & PENALTIES (no GST — not a supply)
    # -------------------------------------------------------------------------

    {"keywords": ["fine", "penalty", "infringement", "parking fine", "speeding fine",
                  "traffic infringement"],
     "categories": ["fines_penalties"],
     "reason": "Fines are not a supply — no GST"},
]

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    return text.lower().strip()


def is_gst_exempt(description: str, item_category: str | None = None) -> bool:
    """
    Return True if the line item is likely GST-free based on:
    - description keyword matching
    - item_category slug matching

    This is a best-effort heuristic. Complex cases should be reviewed manually.
    """
    desc = _normalise(description)
    cat = _normalise(item_category or "")

    for rule in GST_FREE_RULES:
        # Match on description keywords
        if any(_normalise(kw) in desc for kw in rule["keywords"]):
            return True
        # Match on category slug
        if cat and cat in rule["categories"]:
            return True

    return False


def get_exempt_reason(description: str, item_category: str | None = None) -> str | None:
    """Return the ATO exemption reason for a line item, or None if taxable."""
    desc = _normalise(description)
    cat = _normalise(item_category or "")

    for rule in GST_FREE_RULES:
        if any(_normalise(kw) in desc for kw in rule["keywords"]):
            return rule["reason"]
        if cat and cat in rule["categories"]:
            return rule["reason"]

    return None
