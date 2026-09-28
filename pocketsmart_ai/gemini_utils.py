"""
PocketSmart AI: Gemini AI Utility Service & Recommendation Engine
Handles AI prompt orchestration, Google Gemini model integration,
multimodal analysis (text + images), JSON parsing, and dynamic shopping links.
"""

import os
import re
import json
import urllib.parse
from typing import Optional, Dict, Any, List
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
gemini_model = None

try:
    import google.generativeai as genai
    if API_KEY and API_KEY.strip() and API_KEY != "your_gemini_api_key_here":
        genai.configure(api_key=API_KEY.strip())
        # Try finding standard flash model
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    print(f"[PocketSmart AI] Note: Gemini API initialization message: {e}")


def extract_json_from_response(text: str) -> dict:
    """Extract and parse JSON safely from Gemini model output."""
    if not text:
        raise ValueError("Empty response from AI model")

    clean_text = text.strip()
    
    # Strip markdown code fences ```json ... ```
    if "```json" in clean_text:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", clean_text)
        if match:
            clean_text = match.group(1).strip()
    elif "```" in clean_text:
        match = re.search(r"```\s*([\s\S]*?)\s*```", clean_text)
        if match:
            clean_text = match.group(1).strip()

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # Fallback: look for the outermost JSON object { ... }
        match = re.search(r"(\{[\s\S]*\})", clean_text)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Unable to parse JSON from AI response: {text[:200]}...")


def build_shopping_links(category: str, search_terms: str) -> Dict[str, str]:
    """Build platform shopping links based on category and search terms."""
    if not search_terms:
        return {}
    
    q = urllib.parse.quote_plus(search_terms)
    cat = (category or "").lower()

    # Base links available across platforms
    all_links = {
        "amazon": f"https://www.amazon.in/s?k={q}",
        "flipkart": f"https://www.flipkart.com/search?q={q}",
        "ikea": f"https://www.ikea.com/in/en/search/?q={q}",
        "myntra": f"https://www.myntra.com/search?q={q}",
        "ajio": f"https://www.ajio.com/search/?text={q}",
        "swiggy": f"https://www.swiggy.com/search?query={q}",
        "zomato": f"https://www.zomato.com/search?q={q}",
        "bigbasket": f"https://www.bigbasket.com/ps/?q={q}",
        "bookmyshow": f"https://in.bookmyshow.com/search?q={q}",
        "google": f"https://www.google.com/search?q={q}",
        "booking": f"https://www.booking.com/search.html?ss={q}",
        "makemytrip": f"https://www.makemytrip.com/hotels/hotel-listing/?searchText={q}",
        "oyorooms": f"https://www.oyorooms.com/search/?location={q}",
        "nobroker": f"https://www.nobroker.in/property/search/?searchTerm={q}",
        "bluestone": f"https://www.bluestone.com/search.html?query={q}",
        "tanishq": f"https://www.tanishq.co.in/search?q={q}",
        "caratlane": f"https://www.caratlane.com/search?q={q}",
        "melorra": f"https://www.melorra.com/search?q={q}",
        "meesho": f"https://www.meesho.com/search?q={q}"
    }

    category_platforms = {
        "venue": ["google", "booking", "makemytrip", "oyorooms", "nobroker"],
        "food": ["swiggy", "zomato", "bigbasket", "amazon", "flipkart"],
        "catering": ["swiggy", "zomato"],
        "drinks": ["swiggy", "zomato", "bigbasket", "amazon", "flipkart"],
        "decoration": ["amazon", "flipkart", "meesho", "myntra"],
        "entertainment": ["bookmyshow", "amazon", "flipkart"],
        "gifts": ["amazon", "flipkart", "myntra", "meesho"],
        "photography": ["google", "amazon", "flipkart"],
        "music": ["amazon", "flipkart", "bookmyshow"],
        "games": ["amazon", "flipkart"],
        "accessories": ["amazon", "flipkart", "myntra", "meesho"],
        "transportation": ["makemytrip", "google"],
        "return_gifts": ["amazon", "flipkart", "myntra", "meesho"],
        "lighting": ["amazon", "flipkart", "ikea", "myntra", "ajio"],
        "ceiling_fans": ["amazon", "flipkart", "ikea", "myntra", "ajio"],
        "furniture": ["ikea", "amazon", "flipkart", "ajio"],
        "dining": ["ikea", "amazon", "flipkart"],
        "jewelry": ["tanishq", "caratlane", "bluestone", "amazon", "flipkart", "meesho", "melorra"]
    }

    selected_platforms = category_platforms.get(cat, ["amazon", "flipkart", "ikea", "myntra", "ajio"])
    return {p: all_links[p] for p in selected_platforms if p in all_links}


# -------------------------------------------------------------
# 1. HOME INTERIOR RECOMMENDATIONS
# -------------------------------------------------------------
def get_home_recommendations_ai(budget_input) -> dict:
    """Generate home interior budget recommendations via Gemini AI or intelligent fallback."""
    total_budget = float(budget_input.total_budget)
    
    rooms = []
    if getattr(budget_input, 'has_living_room', False):
        rooms.append("Living room")
    if getattr(budget_input, 'has_kitchen', False):
        rooms.append("Kitchen")
    if getattr(budget_input, 'has_bedroom', False):
        rooms.append("Bedroom")
    rooms_text = "\n".join([f"- {r}" for r in rooms]) if rooms else "General Living Space"

    prompt = f"""I need interior design product recommendations for a home in India with a total budget of ₹{total_budget:.2f}.
Requirements:
- {budget_input.num_lights} lights/lighting fixtures
- {budget_input.num_fans} ceiling fans
- {budget_input.num_furniture} furniture pieces
- {budget_input.num_dining_tables} dining tables
Additional rooms to consider:
{rooms_text}
Additional requirements: {budget_input.additional_requirements or "None"}

Please provide a detailed budget breakdown with product recommendations **available in India**.
Use **Indian brands and pricing** (in INR ₹). Include **search terms** suitable for Indian shopping platforms.

Format your response as valid JSON with the following structure:
{{
  "total_budget": {total_budget:.2f},
  "budget_breakdown": [
    {{
      "category": "lighting",
      "allocation": 0.0,
      "items": [
        {{
          "name": "",
          "description": "",
          "estimated_price": 0.0,
          "quantity": 1,
          "search_terms": ""
        }}
      ]
    }}
  ],
  "calculation_table": [
    {{
      "category": "",
      "items_count": 0,
      "total_cost": 0.0,
      "percentage_of_budget": 0.0
    }}
  ],
  "remaining_budget": 0.0,
  "additional_suggestions": [
    "Tip 1",
    "Tip 2"
  ]
}}
Ensure total costs stay strictly within budget. Include search terms for each item to find on shopping websites like Flipkart, Amazon India, IKEA India."""

    result = None
    if gemini_model:
        try:
            response = gemini_model.generate_content(prompt)
            result = extract_json_from_response(response.text)
        except Exception as e:
            print(f"[PocketSmart AI] Gemini call fallback for home planner: {e}")

    # Fallback generator if AI call was not available or failed
    if not result:
        result = _fallback_home_recommendations(budget_input)

    # Attach shopping links to each item
    for category in result.get("budget_breakdown", []):
        cat_name = category.get("category", "home").lower()
        for item in category.get("items", []):
            st = item.get("search_terms") or item.get("name")
            q = urllib.parse.quote_plus(st)
            item["shopping_links"] = {
                "amazon": f"https://www.amazon.in/s?k={q}",
                "flipkart": f"https://www.flipkart.com/search?q={q}",
                "ikea": f"https://www.ikea.com/in/en/search/?q={q}",
                "myntra": f"https://www.myntra.com/search?q={q}",
                "ajio": f"https://www.ajio.com/search/?text={q}"
            }

    return result


def _fallback_home_recommendations(budget_input) -> dict:
    """Intelligent fallback for Home Interior Planner with realistic Indian pricing."""
    budget = float(budget_input.total_budget)
    n_lights = max(1, budget_input.num_lights)
    n_fans = max(0, budget_input.num_fans)
    n_furn = max(0, budget_input.num_furniture)
    n_dining = max(0, budget_input.num_dining_tables)

    # Allocations
    light_budget = min(budget * 0.20, n_lights * 400.0)
    fan_budget = min(budget * 0.30, n_fans * 1600.0) if n_fans else 0.0
    dining_budget = min(budget * 0.25, n_dining * 6000.0) if n_dining else 0.0
    furniture_budget = max(0.0, budget - (light_budget + fan_budget + dining_budget) - 500.0)

    breakdown = []
    calc_table = []
    total_spent = 0.0

    # Lighting
    unit_light = round(light_budget / n_lights, 2) if n_lights else 0.0
    light_cost = unit_light * n_lights
    breakdown.append({
        "category": "Lighting",
        "allocation": light_cost,
        "items": [
            {
                "name": "Philips / Wipro Warm White LED Bulbs (9W)",
                "description": "Energy-efficient LED bulbs with warm ambient illumination for rooms.",
                "estimated_price": unit_light,
                "quantity": n_lights,
                "search_terms": "Philips Warm White LED bulb 9W"
            }
        ]
    })
    total_spent += light_cost
    calc_table.append({
        "category": "Lighting",
        "items_count": n_lights,
        "total_cost": round(light_cost, 2),
        "percentage_of_budget": round((light_cost / budget) * 100, 1)
    })

    # Fans
    if n_fans > 0:
        unit_fan = round(fan_budget / n_fans, 2)
        fan_cost = unit_fan * n_fans
        breakdown.append({
            "category": "Ceiling_fans",
            "allocation": fan_cost,
            "items": [
                {
                    "name": "Havells / Crompton High Speed Ceiling Fan",
                    "description": "Durable, energy-saving 1200mm ceiling fan suitable for bedrooms and halls.",
                    "estimated_price": unit_fan,
                    "quantity": n_fans,
                    "search_terms": "Havells Crompton 1200mm Ceiling Fan"
                }
            ]
        })
        total_spent += fan_cost
        calc_table.append({
            "category": "Ceiling_fans",
            "items_count": n_fans,
            "total_cost": round(fan_cost, 2),
            "percentage_of_budget": round((fan_cost / budget) * 100, 1)
        })

    # Furniture
    if n_furn > 0:
        unit_furn = round(furniture_budget / n_furn, 2) if n_furn else 0.0
        furn_cost = unit_furn * n_furn
        breakdown.append({
            "category": "Furniture",
            "allocation": furn_cost,
            "items": [
                {
                    "name": "IKEA Modern Wooden Lounge Chair / Table Unit",
                    "description": "Sleek, minimalist interior furniture piece engineered for compact spaces.",
                    "estimated_price": unit_furn,
                    "quantity": n_furn,
                    "search_terms": "IKEA wooden modern side table chair"
                }
            ]
        })
        total_spent += furn_cost
        calc_table.append({
            "category": "Furniture",
            "items_count": n_furn,
            "total_cost": round(furn_cost, 2),
            "percentage_of_budget": round((furn_cost / budget) * 100, 1)
        })

    # Dining
    if n_dining > 0:
        dining_cost = dining_budget
        breakdown.append({
            "category": "Dining_tables",
            "allocation": dining_cost,
            "items": [
                {
                    "name": "Compact Engineered Wood Dining Table",
                    "description": "Sturdy 4-seater dining table with waterproof melamine finish.",
                    "estimated_price": round(dining_cost / n_dining, 2),
                    "quantity": n_dining,
                    "search_terms": "Wooden 4 seater dining table"
                }
            ]
        })
        total_spent += dining_cost
        calc_table.append({
            "category": "Dining_tables",
            "items_count": n_dining,
            "total_cost": round(dining_cost, 2),
            "percentage_of_budget": round((dining_cost / budget) * 100, 1)
        })

    remaining = max(0.0, round(budget - total_spent, 2))

    return {
        "total_budget": budget,
        "budget_breakdown": breakdown,
        "calculation_table": calc_table,
        "remaining_budget": remaining,
        "additional_suggestions": [
            "Consider festive sale seasons on Flipkart & Amazon for up to 30% discounts.",
            "Explore IKEA flat-pack furniture to save on shipping and installation charges.",
            "Choose warm 3000K lighting for living spaces and neutral 4000K for study areas.",
            "Prioritize multi-functional furniture items for optimal space utilization."
        ]
    }


# -------------------------------------------------------------
# 2. PARTY BUDGET RECOMMENDATIONS
# -------------------------------------------------------------
def get_party_recommendations_ai(budget_input) -> dict:
    """Generate event and party budget recommendations via Gemini AI or intelligent fallback."""
    total_budget = float(budget_input.total_budget)

    prompt = f"""I need party planning recommendations for India with a total budget of ₹{total_budget:.2f}.
Party details:
- Type: {budget_input.party_type}
- Number of guests: {budget_input.num_guests}
- Venue type: {budget_input.venue_type or "Not specified"}
- Catering needed: {"Yes" if budget_input.needs_catering else "No"}
- Decoration needed: {"Yes" if budget_input.needs_decoration else "No"}
- Entertainment needed: {"Yes" if budget_input.needs_entertainment else "No"}
Additional requirements: {budget_input.additional_requirements or "None"}

Please provide a detailed budget breakdown with specific recommendations available in India using INR prices.
Use Indian brands, services, and typical cost expectations.

Format your response as JSON with the following structure:
{{
  "total_budget": {total_budget:.2f},
  "budget_breakdown": [
    {{
      "category": "venue",
      "allocation": 0.0,
      "items": [
        {{
          "name": "",
          "description": "",
          "estimated_price": 0.0,
          "quantity": 1,
          "search_terms": ""
        }}
      ]
    }}
  ],
  "venue_suggestions": [
    {{
      "name": "Venue Name",
      "type": "Banquet / Home / Lawn",
      "capacity": 50,
      "estimated_cost": 0.0,
      "search_terms": "event hall"
    }}
  ],
  "remaining_budget": 0.0,
  "additional_suggestions": [
    "Suggestion 1",
    "Suggestion 2"
  ]
}}
Ensure all costs are in INR and total does not exceed the given budget.
Provide search terms suitable for Indian websites such as BookMyShow, Swiggy, Flipkart, etc."""

    result = None
    if gemini_model:
        try:
            response = gemini_model.generate_content(prompt)
            result = extract_json_from_response(response.text)
        except Exception as e:
            print(f"[PocketSmart AI] Gemini call fallback for party planner: {e}")

    if not result:
        result = _fallback_party_recommendations(budget_input)

    # Create Calculation Table INR and Shopping Links (PDF Pages 14-16)
    categories_calc = {}
    for cat in result.get("budget_breakdown", []):
        cat_name = cat.get("category", "Misc").capitalize()
        cat_alloc = cat.get("allocation", 0.0)
        items = cat.get("items", [])
        categories_calc[cat_name] = {
            "category": cat_name,
            "items_count": len(items),
            "total_cost": sum([float(i.get("estimated_price", 0.0)) * int(i.get("quantity", 1)) for i in items]) or cat_alloc,
            "percentage_of_budget": 0.0
        }

    total_b = float(result.get("total_budget", total_budget)) or 1.0
    calc_table = []
    for cname, cdata in categories_calc.items():
        if total_b > 0:
            cdata["percentage_of_budget"] = round((cdata["total_cost"] / total_b) * 100, 1)
        calc_table.append(cdata)
    result["calculation_table_inr"] = calc_table

    # Add shopping links for each item (PDF Page 15)
    for category in result.get("budget_breakdown", []):
        cat_name = category.get("category", "").lower()
        for item in category.get("items", []):
            st = item.get("search_terms") or item.get("name", "")
            if st:
                item["shopping_links"] = build_shopping_links(cat_name, st)

    # Add search links for venue suggestions (PDF Page 16)
    for venue in result.get("venue_suggestions", []):
        st = venue.get("search_terms") or venue.get("name", "")
        if st:
            q = urllib.parse.quote_plus(st)
            venue["search_links"] = {
                "google": f"https://www.google.com/search?q={q}",
                "booking": f"https://www.booking.com/search.html?ss={q}",
                "makemytrip": f"https://www.makemytrip.com/hotels/hotel-listing/?searchText={q}",
                "oyorooms": f"https://www.oyorooms.com/search/?location={q}",
                "nobroker": f"https://www.nobroker.in/property/search/?searchTerm={q}"
            }

    return result


def _fallback_party_recommendations(budget_input) -> dict:
    """Fallback generator for Party Budget Planner with realistic event packages."""
    budget = float(budget_input.total_budget)
    guests = max(1, budget_input.num_guests)
    party_type = budget_input.party_type or "Party"
    venue_type = budget_input.venue_type or "Residential"

    # Allocations based on needs
    breakdown = []
    total_spent = 0.0

    # Venue
    venue_cost = 0.0 if "home" in venue_type.lower() else round(budget * 0.20, 2)
    breakdown.append({
        "category": "venue",
        "allocation": venue_cost,
        "items": [
            {
                "name": f"{venue_type} Event Space",
                "description": f"Hosting {guests} guests for {party_type}.",
                "estimated_price": venue_cost,
                "quantity": 1,
                "search_terms": f"{venue_type} party venue"
            }
        ]
    })
    total_spent += venue_cost

    # Catering
    if budget_input.needs_catering:
        cater_cost = round(min(budget * 0.45, guests * 250.0), 2)
        breakdown.append({
            "category": "catering",
            "allocation": cater_cost,
            "items": [
                {
                    "name": "Buffet Meal & Refreshments (Swiggy / Zomato Catering)",
                    "description": f"Multi-course delicious meal platter for {guests} guests with beverages.",
                    "estimated_price": cater_cost,
                    "quantity": 1,
                    "search_terms": "party food catering package"
                }
            ]
        })
        total_spent += cater_cost

    # Decoration
    if budget_input.needs_decoration:
        decor_cost = round(budget * 0.15, 2)
        breakdown.append({
            "category": "decoration",
            "allocation": decor_cost,
            "items": [
                {
                    "name": "Themed Balloon Arch & Fairy Light Decor Kit",
                    "description": f"Festive DIY celebration decor set suited for {party_type}.",
                    "estimated_price": decor_cost,
                    "quantity": 1,
                    "search_terms": f"{party_type} decoration balloon arch kit"
                }
            ]
        })
        total_spent += decor_cost

    # Entertainment
    if budget_input.needs_entertainment:
        ent_cost = round(budget * 0.12, 2)
        breakdown.append({
            "category": "entertainment",
            "allocation": ent_cost,
            "items": [
                {
                    "name": "Portable Bluetooth Speaker & Party Games Pack",
                    "description": "Audio entertainment and engaging interactive group board games.",
                    "estimated_price": ent_cost,
                    "quantity": 1,
                    "search_terms": "party games bluetooth party speaker"
                }
            ]
        })
        total_spent += ent_cost

    remaining = max(0.0, round(budget - total_spent, 2))

    return {
        "total_budget": budget,
        "budget_breakdown": breakdown,
        "venue_suggestions": [
            {
                "name": f"Cosy {venue_type} Club / Hall",
                "type": venue_type,
                "capacity": guests + 10,
                "estimated_cost": venue_cost,
                "search_terms": f"{venue_type} party celebration hall"
            }
        ],
        "remaining_budget": remaining,
        "additional_suggestions": [
            "Consider ordering bulk catering from Swiggy/Zomato for discounted per-plate pricing.",
            "Use reusable fairy lights and paper tassels for eco-friendly budget decoration.",
            "Create curated Spotify or YouTube Music playlists to save on DJ costs.",
            "Send digital invitations via WhatsApp/Canva to save paper and printing expenses."
        ]
    }


# -------------------------------------------------------------
# 3. JEWELRY BUDGET RECOMMENDATIONS (MULTIMODAL: TEXT + IMAGE)
# -------------------------------------------------------------
def get_jewelry_recommendations_ai(budget_input, image_path: Optional[str] = None) -> dict:
    """Generate jewelry recommendations with multimodal outfit analysis (PDF Page 16, 17)."""
    total_budget = float(budget_input.total_budget)
    occasion = budget_input.occasion or "Special Occasion"
    preferences = budget_input.preferences or "Not specified"

    base_prompt = f"""I need jewelry recommendations for India with a total budget of ₹{total_budget:.2f}.
Occasion: {occasion}
Preferences: {preferences}
Provide only India-relevant styles, availability, and price ranges in INR."""

    result = None

    if gemini_model:
        try:
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                prompt = base_prompt + """\nAn image of the outfit is uploaded. Suggest jewelry that complements it, considering color, design, and occasion appropriateness.
Format the output as JSON:
{
  "outfit_analysis": {
    "colors": ["Primary Color", "Secondary Color"],
    "style": "Traditional / Western / Fusion",
    "formality": "Formal / Festive / Casual"
  },
  "total_budget": """ + f"{total_budget:.2f}" + """,
  "jewelry_recommendations": [
    {
      "item_type": "Necklace / Earrings / Bracelet / Ring",
      "description": "Elegant design description",
      "style": "Contemporary / Ethnic / Minimalist",
      "estimated_price": 0.0,
      "search_terms": "gold plated choker necklace"
    }
  ],
  "remaining_budget": 0.0,
  "styling_tips": [
    "Styling tip 1",
    "Styling tip 2"
  ]
}
Make sure prices are in INR and stay within budget. Include Indian-friendly search terms for shopping."""
                response = gemini_model.generate_content([prompt, img])
                result = extract_json_from_response(response.text)
            else:
                prompt = base_prompt + """\nFormat the output as JSON:
{
  "total_budget": """ + f"{total_budget:.2f}" + """,
  "jewelry_recommendations": [
    {
      "item_type": "Necklace / Earrings / Bracelet / Ring",
      "description": "Design description matching occasion",
      "style": "Traditional / Minimalist",
      "estimated_price": 0.0,
      "search_terms": "oxidised silver jhumkas"
    }
  ],
  "remaining_budget": 0.0,
  "styling_tips": [
    "Styling tip 1",
    "Styling tip 2"
  ]
}
Keep prices in INR and relevant to Indian brands."""
                response = gemini_model.generate_content(prompt)
                result = extract_json_from_response(response.text)
        except Exception as e:
            print(f"[PocketSmart AI] Gemini call fallback for jewelry planner: {e}")

    if not result:
        result = _fallback_jewelry_recommendations(budget_input, image_path)

    # Attach India-specific shopping links (PDF Page 17)
    for item in result.get("jewelry_recommendations", []):
        st = item.get("search_terms") or f"{item.get('item_type', '')} {item.get('style', '')}"
        q = urllib.parse.quote_plus(st)
        item["shopping_links"] = {
            "amazon": f"https://www.amazon.in/s?k={q}",
            "flipkart": f"https://www.flipkart.com/search?q={q}",
            "bluestone": f"https://www.bluestone.com/search.html?query={q}",
            "tanishq": f"https://www.tanishq.co.in/search?q={q}",
            "caratlane": f"https://www.caratlane.com/search?q={q}",
            "melorra": f"https://www.melorra.com/search?q={q}",
            "meesho": f"https://www.meesho.com/search?q={q}"
        }

    return result


def _fallback_jewelry_recommendations(budget_input, image_path: Optional[str] = None) -> dict:
    """Fallback generator for Jewelry Budget Planner with styling insight."""
    budget = float(budget_input.total_budget)
    occasion = (budget_input.occasion or "Celebration").title()
    has_image = bool(image_path and os.path.exists(image_path))

    # Split budget across 3 complementary jewelry items
    p1 = round(budget * 0.45, 2)
    p2 = round(budget * 0.30, 2)
    p3 = round(budget * 0.15, 2)
    remaining = max(0.0, round(budget - (p1 + p2 + p3), 2))

    analysis = None
    if has_image:
        analysis = {
            "colors": ["Royal Blue", "Warm Gold / Silver Accents"],
            "style": "Indo-Western / Festive",
            "formality": f"Formal ({occasion})"
        }

    recommendations = [
        {
            "item_type": "Necklace / Pendant",
            "description": f"Elegant statement piece designed for {occasion} with intricate craftsmanship.",
            "style": "Contemporary Ethnic",
            "estimated_price": p1,
            "search_terms": f"{occasion} choker necklace pendant"
        },
        {
            "item_type": "Earrings / Jhumkas",
            "description": "Complementary drop earrings with lightweight design for all-day comfort.",
            "style": "Traditional Filigree",
            "estimated_price": p2,
            "search_terms": f"traditional {occasion} designer earrings"
        },
        {
            "item_type": "Bracelet / Bangle / Ring",
            "description": "Delicate adjustable cuff or cocktail ring that adds subtle elegance.",
            "style": "Minimalist Chic",
            "estimated_price": p3,
            "search_terms": "adjustable gemstone cocktail ring bracelet"
        }
    ]

    res = {
        "total_budget": budget,
        "jewelry_recommendations": recommendations,
        "remaining_budget": remaining,
        "styling_tips": [
            f"Balance your jewelry: if wearing an elaborate necklace, pair it with subtle stud earrings for {occasion}.",
            "Match your metal undertones: Gold and brass jewelry complement warm palettes, while silver and platinum suit cool tones.",
            "Check BlueStone and CaratLane for BIS-hallmarked and certified designs within your budget.",
            "Store fashion jewelry in dry, airtight pouches to maintain luster and avoid tarnishing."
        ]
    }
    if analysis:
        res["outfit_analysis"] = analysis

    return res
