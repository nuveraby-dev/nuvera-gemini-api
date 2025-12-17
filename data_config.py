import json

def get_price_json_string():
    # Мы используем сверхкомпактный формат для экономии квоты API
    price_data = {
        "BW_PRINT_A4": "0.50 (1-10), 0.42 (11-50), 0.36 (51-100), 0.30 (101-300), 0.24 (301+)",
        "BW_PRINT_A3": "1.00 (1-10), 0.84 (11-50), 0.72 (51-100), 0.60 (101-300), 0.48 (301+)",
        "COLOR_PRINT_A4": "1.40 (1-10), 1.20 (11-50), 1.14 (51-100), 1.08 (101-300), 0.90 (301+)",
        "BLUEPRINTS_BW": {"A2": 1.80, "A1": 3.00, "A0": 6.00},
        "PAPER_SRA3": {
            "Coated": "0.24-0.96", 
            "Design_Natural": "1.8-2.1",
            "Design_Texture": "1.08-2.7", 
            "Metallic": "1.2-3.6",
            "Stickers": "2.4-5.4"
        },
        "PHOTO_DOCS": "15.00",
        "PHOTO_PRINT": {"10x15": "0.78-0.96", "A4": 2.70},
        "BUSINESS_CARDS_96": {"Standard": "24-30", "Texture": "27-38.4", "Metallic": "30-39.6"},
        "OFFSET_1000": {"Flyers": 120, "Leaflets_A6-A4": "96-315"},
        "POST_PRINT": {"Folding": "0.18-1.08", "Cutting": 0.36, "Lam_A4": 2.1},
        "COEFFS": "ID-Passport x1.3, Double-sided x2, Fill >50% x1.3"
    }
    # dump без indent экономит еще 15-20% лимита
    return json.dumps(price_data, ensure_ascii=False)
