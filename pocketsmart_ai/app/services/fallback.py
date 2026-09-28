from .catalog import home_catalog, party_catalog, jewelry_catalog, search_url
from ..models.schemas import RecommendationResponse, RecommendationItem

def _pick(items, budget, quantity=1):
    out=[]
    remaining=budget
    for name, category, platform, price in items:
        if price == 0 or price * quantity <= max(remaining, 0) or not out:
            shown = price * quantity if price else 0
            out.append(RecommendationItem(name=name, category=category, platform=platform,
                price=shown, reason="Selected as a practical starting option for the requested category and budget.",
                url=search_url(platform, name), budget_fit="compare current listing price" if price == 0 else "within budget"))
            if price: remaining -= shown
        if len(out) >= 6: break
    return out

def home_fallback(data):
    allocations = {"furniture": round(data.budget*.40,2), "lighting": round(data.budget*.20,2), "decor": round(data.budget*.20,2), "storage": round(data.budget*.20,2)}
    recs=[]
    for item in data.items:
        recs.extend(_pick([x for x in home_catalog(data.style) if x[1] == item.category] or home_catalog(data.style), allocations.get("furniture", data.budget)/max(len(data.items),1), item.quantity))
    return RecommendationResponse(planner="home", budget=data.budget, allocations=allocations,
        summary=f"A {data.style} {data.room} plan for ₹{data.budget:,.0f}, balancing the requested items across major categories.",
        recommendations=recs[:8], tips=["Check measurements before buying furniture.", "Keep a small buffer for delivery and installation.", "Compare the final live price before purchase."])

def party_fallback(data):
    allocations={"food":round(data.budget*.50,2),"venue":round(data.budget*.20,2),"decoration":round(data.budget*.15,2),"entertainment":round(data.budget*.15,2)}
    recs=_pick(party_catalog(data.event_type), data.budget)
    return RecommendationResponse(planner="party", budget=data.budget, allocations=allocations,
        summary=f"A {data.event_type} plan for {data.guests} guests with a ₹{data.budget:,.0f} budget.", recommendations=recs,
        tips=["Confirm per-person food pricing and delivery charges.", "Reserve venue capacity for the full guest count.", "Keep 5–10% of the budget as a contingency if possible."])

def jewelry_fallback(data):
    recs=_pick(jewelry_catalog(data.style, data.material), data.budget)
    return RecommendationResponse(planner="jewelry", budget=data.budget,
        allocations={"jewelry":data.budget},
        summary=f"{data.style.title()} jewelry ideas for a {data.occasion} within ₹{data.budget:,.0f}. Outfit color: {data.outfit_color or 'not specified'}.",
        recommendations=recs, tips=["Match metal tone with the outfit and occasion.", "For an image-based match, use the uploaded outfit as a style reference only.", "Verify material, size, return policy, and current price before ordering."])
