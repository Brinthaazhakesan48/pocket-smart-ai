import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..config import get_settings
from ..db import get_db
from ..dependencies import current_user
from ..models.schemas import HomeRequest, JewelryRequest, PartyRequest
from ..services.recommendations import generate


router = APIRouter(
    prefix="/api",
    tags=["recommendations"],
)


def _size_ok(data: bytes) -> None:
    max_size = get_settings().max_upload_mb * 1024 * 1024

    if len(data) > max_size:
        raise HTTPException(
            status_code=413,
            detail="Image is too large",
        )


@router.post("/generate-home")
def home(
    data: HomeRequest,
    user=Depends(current_user),
):
    return generate(
        "home",
        data,
        user["id"],
    )


@router.post("/generate-party")
def party(
    data: PartyRequest,
    user=Depends(current_user),
):
    return generate(
        "party",
        data,
        user["id"],
    )


@router.post("/generate-jewelry")
async def jewelry(
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form("elegant"),
    outfit_color: str = Form(""),
    material: str = Form("any"),
    image: UploadFile | None = File(None),
    user=Depends(current_user),
):
    data = JewelryRequest(
        budget=budget,
        occasion=occasion,
        style=style,
        outfit_color=outfit_color,
        material=material,
    )

    image_bytes = None
    mime = "image/jpeg"

    if image:
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        if image.content_type not in allowed_types:
            raise HTTPException(
                status_code=415,
                detail="Use JPG, PNG, or WebP",
            )

        image_bytes = await image.read()
        _size_ok(image_bytes)

        mime = image.content_type

    return generate(
        "jewelry",
        data,
        user["id"],
        image_bytes,
        mime,
    )


@router.get("/recommendations-details/{recommendation_id}")
def details(
    recommendation_id: int,
    user=Depends(current_user),
):
    with get_db() as db:
        row = db.execute(
            """
            SELECT *
            FROM recommendations
            WHERE id = ? AND user_id = ?
            """,
            (recommendation_id, user["id"]),
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found",
        )

    return {
        "id": row["id"],
        "planner": row["planner"],
        "created_at": row["created_at"],
        "request": json.loads(row["request_json"]),
        "response": json.loads(row["response_json"]),
    }


@router.get("/history")
def history(user=Depends(current_user)):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT id, planner, request_json, response_json, created_at
            FROM recommendations
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user["id"],),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "planner": row["planner"],
            "created_at": row["created_at"],
            "request": json.loads(row["request_json"]),
            "response": json.loads(row["response_json"]),
        }
        for row in rows
    ]

