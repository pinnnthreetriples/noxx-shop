"""Admin auto-translate endpoint."""
from fastapi import APIRouter, HTTPException

from app.modules.admin_api.translate.service import LANGUAGES, TranslationError, translate_to_all

router = APIRouter(tags=["admin-translate"])


@router.post("/translate")
async def translate(payload: dict):
    """Body: {text, source}. Returns {translations: {lang: text}} for all UI languages."""
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    source = payload.get("source") or "en"
    try:
        translations = await translate_to_all(text, source)
    except TranslationError as e:
        raise HTTPException(status_code=502, detail=f"Translation failed: {e}") from e
    return {"translations": translations, "languages": list(LANGUAGES)}
