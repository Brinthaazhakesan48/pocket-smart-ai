from urllib.parse import quote_plus

PLATFORMS = {
    "Amazon": "https://www.amazon.in/s?k={q}",
    "Flipkart": "https://www.flipkart.com/search?q={q}",
    "IKEA": "https://www.ikea.com/in/en/search/?q={q}",
    "Swiggy": "https://www.swiggy.com/search?query={q}",
    "Zomato": "https://www.zomato.com/search?q={q}",
    "OYO": "https://www.oyorooms.com/search?location={q}",
}

def search_url(platform: str, query: str) -> str:
    return PLATFORMS.get(platform, "https://www.google.com/search?q={q}").format(q=quote_plus(query))

def home_catalog(style: str):
    return [
        ("LED Ceiling Light", "lighting", "IKEA", 1499),
        ("Smart LED Bulb 4-Pack", "lighting", "Amazon", 1299),
        ("Ceiling Fan 1200mm", "fan", "Flipkart", 2399),
        ("Compact 4-Seater Dining Set", "dining", "IKEA", 8999),
        ("Minimal Wall Art Set", "decor", "Amazon", 1599),
        ("Storage Cabinet", "storage", "Flipkart", 4999),
        ("Accent Cushion Set", "decor", "IKEA", 999),
    ]

def party_catalog(event_type: str):
    return [
        ("Party Catering Search", "catering", "Swiggy", 0),
        ("Restaurant / Catering Search", "catering", "Zomato", 0),
        ("Venue & Stay Search", "venue", "OYO", 0),
        ("Party Decoration Kit", "decoration", "Amazon", 1299),
        ("Disposable Tableware Set", "decoration", "Flipkart", 799),
        ("Event Lighting Set", "entertainment", "Amazon", 1699),
    ]

def jewelry_catalog(style: str, material: str):
    return [
        ("Minimal Necklace Set", "necklace", "Amazon", 899),
        ("Statement Earrings", "earrings", "Flipkart", 699),
        ("Classic Bracelet", "bracelet", "Amazon", 799),
        ("Elegant Pendant", "pendant", "Flipkart", 1199),
        ("Traditional Jhumka Pair", "earrings", "Amazon", 999),
    ]
