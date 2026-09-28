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
from .fallback import home_fallback, party_fallback, jewelry_fallback

class GeminiService:
    def __init__(self):
        s=get_settings()
        self.enabled=bool(s.ai_enabled and s.gemini_api_key and genai is not None and types is not None)
        self.model=s.gemini_model
        self.client=genai.Client(api_key=s.gemini_api_key) if self.enabled else None

    def _prompt(self, planner: str, data: Any, catalog_text: str, image_note: str = "") -> str:
        return f"""You are PocketSmart AI, a budget planning assistant. Planner: {planner}.\nUser data: {data.model_dump_json()}\nAvailable catalog/search options: {catalog_text}\n{image_note}\nReturn only valid JSON matching the supplied response schema. Do not invent live prices or claim an item is in stock. Use only the listed platform names and create recommendations using their search URLs supplied by the server. Keep the total of non-zero estimated item prices at or below the budget when practical. This is a planning aid, not financial advice."""

    def generate(self, planner: str, data: Any, catalog_text: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> RecommendationResponse:
        if not self.enabled:
            return {"home": home_fallback, "party": party_fallback, "jewelry": jewelry_fallback}[planner](data)
        contents=[self._prompt(planner,data,catalog_text, "An outfit image is attached. Consider visible colors/styles without identifying the person." if image_bytes else "")]
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        try:
            response=self.client.models.generate_content(model=self.model, contents=contents,
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=RecommendationResponse, temperature=0.4, max_output_tokens=3000))
            parsed=getattr(response,"parsed",None)
            if parsed is not None:
                result=parsed if isinstance(parsed, RecommendationResponse) else RecommendationResponse.model_validate(parsed)
            else:
                result=RecommendationResponse.model_validate(json.loads(response.text))
            result.planner=planner; result.budget=data.budget; result.source="gemini"
            return result
        except Exception:
            fallback={"home": home_fallback, "party": party_fallback, "jewelry": jewelry_fallback}[planner](data)
            fallback.source="fallback"
            return fallback
