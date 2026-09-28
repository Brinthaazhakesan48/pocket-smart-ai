from .catalog import (
    home_catalog,
    party_catalog,
    jewelry_catalog,
    search_url,
)

from ..models.schemas import (
    RecommendationResponse,
    RecommendationItem,
)


def _pick(items, budget, quantity=1):
    recommendations = []
    remaining = max(budget, 0)

    for name, category, platform, price in items:
        total_price = price * quantity if price else 0

        # Search-only recommendations have no fixed price.
        if price == 0:
            recommendations.append(
                RecommendationItem(
                    name=name,
                    category=category,
                    platform=platform,
                    price=0,
                    reason=(
                        "Selected as a practical starting option "
                        "for the requested category and budget."
                    ),
                    url=search_url(platform, name),
                    budget_fit="compare current listing price",
                )
            )

        # Fixed-price recommendation must fit the remaining budget.
        elif total_price <= remaining:
            recommendations.append(
                RecommendationItem(
                    name=name,
                    category=category,
                    platform=platform,
                    price=total_price,
                    reason=(
                        "Selected as a practical starting option "
                        "for the requested category and budget."
                    ),
                    url=search_url(platform, name),
                    budget_fit="within budget",
                )
            )

            remaining -= total_price

        if len(recommendations) >= 6:
            break

    return recommendations


def home_fallback(data):
    allocations = {
        "furniture": round(data.budget * 0.40, 2),
        "lighting": round(data.budget * 0.20, 2),
        "decor": round(data.budget * 0.20, 2),
        "storage": round(data.budget * 0.20, 2),
    }

    recommendations = []

    for item in data.items:
        category_items = [
            product
            for product in home_catalog(data.style)
            if product[1] == item.category
        ]

        if not category_items:
            category_items = home_catalog(data.style)

        category_budget = allocations.get(
            item.category,
            data.budget / max(len(data.items), 1),
        )

        recommendations.extend(
            _pick(
                category_items,
                category_budget,
                item.quantity,
            )
        )

    return RecommendationResponse(
        planner="home",
        budget=data.budget,
        allocations=allocations,
        summary=(
            f"A {data.style} {data.room} plan for "
            f"₹{data.budget:,.0f}, balancing the requested "
            "items across major categories."
        ),
        recommendations=recommendations[:8],
        tips=[
            "Check measurements before buying furniture.",
            "Keep a small buffer for delivery and installation.",
            "Compare the final live price before purchase.",
        ],
    )


def party_fallback(data):
    allocations = {
        "food": round(data.budget * 0.50, 2),
        "venue": round(data.budget * 0.20, 2),
        "decoration": round(data.budget * 0.15, 2),
        "entertainment": round(data.budget * 0.15, 2),
    }

    recommendations = _pick(
        party_catalog(data.event_type),
        data.budget,
    )

    return RecommendationResponse(
        planner="party",
        budget=data.budget,
        allocations=allocations,
        summary=(
            f"A {data.event_type} plan for {data.guests} guests "
            f"with a ₹{data.budget:,.0f} budget."
        ),
        recommendations=recommendations,
        tips=[
            "Confirm per-person food pricing and delivery charges.",
            "Reserve venue capacity for the full guest count.",
            "Keep 5–10% of the budget as a contingency if possible.",
        ],
    )


def jewelry_fallback(data):
    recommendations = _pick(
        jewelry_catalog(data.style, data.material),
        data.budget,
    )

    return RecommendationResponse(
        planner="jewelry",
        budget=data.budget,
        allocations={
            "jewelry": data.budget,
        },
        summary=(
            f"{data.style.title()} jewelry ideas for a "
            f"{data.occasion} within ₹{data.budget:,.0f}. "
            f"Outfit color: {data.outfit_color or 'not specified'}."
        ),
        recommendations=recommendations,
        tips=[
            "Match metal tone with the outfit and occasion.",
            "For an image-based match, use the uploaded outfit "
            "as a style reference only.",
            "Verify material, size, return policy, and current "
            "price before ordering.",
        ],
    )
