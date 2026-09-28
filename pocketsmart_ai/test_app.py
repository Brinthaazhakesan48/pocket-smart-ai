"""
Automated End-to-End Test Suite for PocketSmart AI
Tests all routes, authentication, sessions, and planners.
"""

from fastapi.testclient import TestClient
from app import app
import json

client = TestClient(app)

def test_all():
    print("[1/10] Testing Landing Page...")
    r = client.get("/")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "PocketSmart" in r.text
    print("  -> OK")

    print("[2/10] Testing Login & Register Pages...")
    r = client.get("/login")
    assert r.status_code == 200
    assert "Welcome Back" in r.text

    r = client.get("/register")
    assert r.status_code == 200
    assert "Create Your Account" in r.text
    print("  -> OK")

    print("[3/10] Testing Authentication (/token endpoint)...")
    r = client.post("/token", data={"username": "demo", "password": "password123"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token_data = r.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  -> OK (Token generated: {token[:15]}...)")

    print("[4/10] Testing Protected Dashboard (/dashboard)...")
    r = client.get("/dashboard", headers=headers)
    assert r.status_code == 200
    assert "Welcome" in r.text
    print("  -> OK")

    print("[5/10] Testing Home Planner HTML & API (/home-budget)...")
    r = client.get("/home-planner", headers=headers)
    assert r.status_code == 200

    home_payload = {
        "total_budget": 30000.0,
        "num_lights": 6,
        "num_fans": 3,
        "num_furniture": 2,
        "num_dining_tables": 1,
        "has_living_room": True,
        "has_kitchen": True,
        "has_bedroom": True,
        "additional_requirements": "Warm lighting and modern minimalist theme"
    }
    r = client.post("/home-budget", json=home_payload, headers=headers)
    assert r.status_code == 200, f"Home budget failed: {r.text}"
    home_data = r.json()
    assert "budget_breakdown" in home_data
    assert "remaining_budget" in home_data
    # Verify shopping links exist
    first_item = home_data["budget_breakdown"][0]["items"][0]
    assert "shopping_links" in first_item
    assert "amazon" in first_item["shopping_links"]
    assert "flipkart" in first_item["shopping_links"]
    assert "ikea" in first_item["shopping_links"]
    print("  -> OK (Home recommendation generated successfully)")

    print("[6/10] Testing Party Planner HTML & API (/party-budget)...")
    r = client.get("/party-planner", headers=headers)
    assert r.status_code == 200

    party_payload = {
        "total_budget": 15000.0,
        "num_guests": 20,
        "party_type": "Birthday",
        "venue_type": "Home",
        "needs_catering": True,
        "needs_decoration": True,
        "needs_entertainment": True,
        "additional_requirements": "Theme: Pastel blue, vegetarian appetizers"
    }
    r = client.post("/party-budget", json=party_payload, headers=headers)
    assert r.status_code == 200, f"Party budget failed: {r.text}"
    party_data = r.json()
    assert "budget_breakdown" in party_data
    assert "remaining_budget" in party_data
    assert "venue_suggestions" in party_data
    print("  -> OK (Party recommendation generated successfully)")

    print("[7/10] Testing Jewelry Planner HTML & API (/jewelry-budget)...")
    r = client.get("/jewelry-planner", headers=headers)
    assert r.status_code == 200

    jewelry_form = {
        "total_budget": "8000.0",
        "occasion": "Wedding Reception",
        "preferences": "Traditional Kundan with gold tones"
    }
    r = client.post("/jewelry-budget", data=jewelry_form, headers=headers)
    assert r.status_code == 200, f"Jewelry budget failed: {r.text}"
    jewelry_data = r.json()
    assert "jewelry_recommendations" in jewelry_data
    assert len(jewelry_data["jewelry_recommendations"]) > 0
    # Verify Indian jewelry platforms
    j_item = jewelry_data["jewelry_recommendations"][0]
    assert "tanishq" in j_item["shopping_links"]
    assert "bluestone" in j_item["shopping_links"]
    assert "caratlane" in j_item["shopping_links"]
    print("  -> OK (Jewelry recommendation generated successfully)")

    print("[8/11] Testing Multimodal Jewelry Planner with Image Upload...")
    from PIL import Image
    import io
    img = Image.new('RGB', (100, 100), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    files = {'image': ('test_outfit.jpg', buf, 'image/jpeg')}
    form_with_img = {
        "total_budget": "15000.0",
        "occasion": "Engagement Ceremony",
        "preferences": "Sapphire blue matching set"
    }
    r = client.post("/jewelry-budget", data=form_with_img, files=files, headers=headers)
    assert r.status_code == 200
    j_img_data = r.json()
    assert "outfit_analysis" in j_img_data
    assert "jewelry_recommendations" in j_img_data
    print("  -> OK (Multimodal image analysis verified)")

    print("[9/11] Testing Recommendation History (/recommendation-history & /history)...")
    r = client.get("/history", headers=headers)
    assert r.status_code == 200

    r = client.get("/recommendation-history", headers=headers)
    assert r.status_code == 200
    hist_data = r.json()
    assert "history" in hist_data
    assert len(hist_data["history"]) >= 4
    rec_id = hist_data["history"][0]["id"]
    print(f"  -> OK (Total {len(hist_data['history'])} history entries saved)")

    print("[10/11] Testing Recommendation Details (/recommendation-details/{id})...")
    r = client.get(f"/recommendation-details/{rec_id}", headers=headers)
    assert r.status_code == 200
    details = r.json()
    assert details["id"] == rec_id
    print("  -> OK (Recommendation details retrieved successfully)")

    print("[11/11] Testing Session Info (/session-info)...")
    r = client.get("/session-info", headers=headers)
    assert r.status_code == 200
    sess = r.json()
    assert sess["username"] == "demo"
    assert "user_data" in sess
    print("  -> OK (Active session tracking verified)")

    print("\n" + "="*55)
    print("  ALL 11 VERIFICATION TESTS PASSED WITH 0 ERRORS!")
    print("="*55 + "\n")

if __name__ == "__main__":
    test_all()
