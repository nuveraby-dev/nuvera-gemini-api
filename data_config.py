import json

def get_price_json_string():
    # Мы переводим прайс в формат "Ключ: Значение". 
    # Это экономит 80% объема памяти ИИ.
    price_data = {
        "BW_PRINT_A4": {"1-10": 0.50, "11-50": 0.42, "51-100": 0.36, "101-300": 0.30, "301+": 0.24},
        "BW_PRINT_A3": {"1-10": 1.00, "11-50": 0.84, "51-100": 0.72, "101-300": 0.60, "301+": 0.48},
        "COLOR_PRINT_A4": {"1-10": 1.40, "11-50": 1.20, "51-100": 1.14, "101-300": 1.08, "301+": 0.90},
        "COLOR_PRINT_A3": {"1-10": 2.80, "11-50": 2.40, "51-100": 2.28, "101-300": 2.16, "301+": 1.80},
        "BLUEPRINTS_BW": {
            "A2": 1.80, "A1": 3.00, "A0": 6.00, 
            "A4xN": "0.72*N", "A3xN": "1.20*N"
        },
        "PAPER_SRA3": {
            "Coated_130-350g": "0.24-0.96",
            "Designer_Natural": {"250g": 1.80, "300g": 2.10},
            "Designer_Texture": {"120g": 1.08, "250g": 2.40, "300g": 2.70},
            "Metallic": {"120g": 1.20, "250g": 2.70, "300g": 3.60},
            "Sticker_Paper": 2.40, "Sticker_Film": 4.80
        },
        "PHOTO": {
            "Passport": 15.00, "10x15": "0.78-0.96", "A4": 2.70
        },
        "BUSINESS_CARDS_96pcs": {
            "Standard_350g": "24.00 (4+0) / 30.00 (4+4)",
            "Laminated_matte": 38.00,
            "Texture_300g": "27.00 / 38.40",
            "Metallic_300g": "30.00 / 39.60"
        },
        "OFFSET_1000pcs": {
            "Cards_Laminated": "90.00-144.00",
            "Flyer_99x210": 120.00,
            "Leaflet_A6_A5_A4": "96 / 168 / 315"
        },
        "POST_PRINT": {
            "Folding_A3-A0": "0.18-1.08",
            "Cutting_1_cut": 0.36,
            "Lamination_A4": "2.10-3.60",
            "Binding_Plastic_A4": "4.20-7.20"
        },
        "RULES": [
            "ID_Passport_Copy: coeff 1.3",
            "Double_sided_print: price x2",
            "Full_fill_color_50plus: coeff 1.3",
            "Old_blueprints_scan: coeff 1.2"
        ]
    }
    return json.dumps(price_data, ensure_ascii=False)
