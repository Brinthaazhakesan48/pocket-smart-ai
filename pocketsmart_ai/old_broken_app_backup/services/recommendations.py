from .gemini import GeminiService
from .catalog import (
    home_catalog,
    party_catalog,
    jewelry_catalog,
)
from ..db import get_db


ai = GeminiService()


def generate(
    planner,
    data,
    user_id,
    image_bytes=None,
    mime_type="image/jpeg",
):
    if planner == "home":
        catalog = home_catalog(data.style)

    elif planner == "party":
        catalog = party_catalog(data.event_type)

    elif planner == "jewelry":
        catalog = jewelry_catalog(data.style, data.material)

    else:
        raise ValueError(f"Unsupported planner: {planner}")

    catalog_text = str(catalog)

    result = ai.generate(
        planner,
        data,
        catalog_text,
        image_bytes,
        mime_type,
    )

    with get_db() as db:
        db.execute(
            """
            INSERT INTO recommendations(
                user_id,
                planner,
                request_json,
                response_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                planner,
                data.model_dump_json(),
                result.model_dump_json(),
            ),
        )

    return result

