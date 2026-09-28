import json
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from ..config import get_settings
from ..models.schemas import RecommendationResponse
from .fallback import (
    home_fallback,
    party_fallback,
    jewelry_fallback,
)


FALLBACKS = {
    "home": home_fallback,
    "party": party_fallback,
    "jewelry": jewelry_fallback,
}


class GeminiService:
    def __init__(self):
        settings = get_settings()

        self.enabled = bool(
            settings.ai_enabled
            and settings.gemini_api_key
            and genai is not None
            and types is not None
        )

        self.model = settings.gemini_model

        self.client = (
            genai.Client(api_key=settings.gemini_api_key)
            if self.enabled
            else None
        )

    def _prompt(
        self,
        planner: str,
        data: Any,
        catalog_text: str,
        image_note: str = "",
    ) -> str:
        return f"""
You are PocketSmart AI, a budget planning assistant.

Planner: {planner}

User data:
{data.model_dump_json()}

Available catalog/search options:
{catalog_text}

{image_note}

Return only valid JSON matching the supplied response schema.

Rules:
- Do not invent live prices.
- Do not claim that an item is currently in stock.
- Use only the listed platform names.
- Do not invent product URLs.
- Keep the total of non-zero estimated item prices at or below the user's budget when practical.
- Treat catalog prices as estimates, not live prices.
- This is a planning aid, not financial advice.
""".strip()

    def generate(
        self,
        planner: str,
        data: Any,
        catalog_text: str,
        image_bytes: bytes | None = None,
        mime_type: str = "image/jpeg",
    ) -> RecommendationResponse:

        if planner not in FALLBACKS:
            raise ValueError(f"Unsupported planner: {planner}")

        fallback_function = FALLBACKS[planner]

        # Use fallback when Gemini is unavailable.
        if not self.enabled:
            return fallback_function(data)

        image_note = ""

        if image_bytes:
            image_note = (
                "An outfit image is attached. "
                "Consider visible colors and styles only. "
                "Do not identify the person."
            )

        contents = [
            self._prompt(
                planner,
                data,
                catalog_text,
                image_note,
            )
        ]

        if image_bytes:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
            )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RecommendationResponse,
                    temperature=0.4,
                    max_output_tokens=3000,
                ),
            )

            parsed = getattr(response, "parsed", None)

            if parsed is not None:
                if isinstance(parsed, RecommendationResponse):
                    result = parsed
                else:
                    result = RecommendationResponse.model_validate(parsed)

            else:
                result = RecommendationResponse.model_validate(

