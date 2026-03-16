"""
AgriSense AI — FastAPI Backend
================================
Deployed on DigitalOcean App Platform.
Handles web, SMS (Africa's Talking), and WhatsApp (Meta Cloud API) channels.
"""

import os
import json
import httpx
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional

from agents.orchestrator import process_farmer_query

app = FastAPI(
    title="AgriSense AI API",
    description="Multi-agent precision agriculture platform powered by DigitalOcean Gradient™ AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── MODELS ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    farmer_id: str = "anonymous"
    channel: str = "web"
    language: str = "auto"
    location: Optional[dict] = None
    conversation_history: Optional[list] = None


class ChatResponse(BaseModel):
    response: str
    agent_used: str
    language_detected: str
    sources: list
    trace_id: str


# ─── WEB CHAT API ────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat endpoint for web and mobile app.
    Routes to Mama Shamba orchestrator → specialist agents.
    """
    try:
        result = process_farmer_query(
            message=req.message,
            farmer_id=req.farmer_id,
            channel=req.channel,
            language=req.language,
            location=req.location,
            conversation_history=req.conversation_history,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/diagnose")
async def diagnose_from_photo(
    image: UploadFile = File(...),
    crop_name: str = Form(...),
    symptoms: str = Form(...),
    farmer_id: str = Form("anonymous"),
    lat: float = Form(None),
    lng: float = Form(None),
    region: str = Form(""),
):
    """
    Crop disease diagnosis from photo.
    Uses GPT-4o vision via Gradient AI serverless inference.
    """
    from agents.crop_doctor import diagnose_from_photo as _diagnose
    
    image_bytes = await image.read()
    location = {"lat": lat, "lng": lng, "region": region} if lat else None
    
    try:
        result = _diagnose(
            image_bytes=image_bytes,
            crop_name=crop_name,
            symptoms_description=symptoms,
            location=location,
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── SMS WEBHOOK (Africa's Talking) ──────────────────────────────────────────

@app.post("/webhooks/sms")
async def sms_webhook(request: Request):
    """
    Handle inbound SMS from Africa's Talking.
    All of Sub-Saharan Africa accessible via basic SMS — no smartphone needed.
    """
    form = await request.form()
    
    phone_number = form.get("from", "")
    message_text = form.get("text", "")
    shortcode = form.get("to", "")
    
    if not message_text:
        return PlainTextResponse("")
    
    # Process via Mama Shamba
    result = process_farmer_query(
        message=message_text,
        farmer_id=phone_number,
        channel="sms",
        language="auto",
    )
    
    # SMS responses must be ≤160 chars
    sms_response = truncate_for_sms(result["response"])
    
    # Reply via Africa's Talking
    await send_sms(phone_number, sms_response)
    
    return PlainTextResponse("")


async def send_sms(to: str, message: str):
    """Send SMS reply via Africa's Talking API."""
    async with httpx.AsyncClient() as http:
        await http.post(
            "https://api.africastalking.com/version1/messaging",
            data={
                "username": os.environ.get("AT_USERNAME", "sandbox"),
                "to": to,
                "message": message,
                "from": os.environ.get("AT_SHORTCODE", "AgriSense"),
            },
            headers={
                "apiKey": os.environ.get("AFRICASTALKING_API_KEY", ""),
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )


def truncate_for_sms(text: str, max_chars: int = 155) -> str:
    """Truncate response to fit SMS limit, keeping it meaningful."""
    if len(text) <= max_chars:
        return text
    # Truncate at last sentence boundary before limit
    truncated = text[:max_chars]
    last_period = truncated.rfind(".")
    if last_period > 80:
        return truncated[:last_period + 1]
    return truncated[:max_chars - 3] + "..."


# ─── WHATSAPP WEBHOOK (Meta Cloud API) ───────────────────────────────────────

WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "agrisense-verify-token")

@app.get("/webhooks/whatsapp")
async def whatsapp_verify(request: Request):
    """WhatsApp webhook verification."""
    params = dict(request.query_params)
    if params.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Invalid verify token")


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle inbound WhatsApp messages."""
    body = await request.json()
    
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        if "messages" not in value:
            return JSONResponse(content={"status": "ok"})
        
        msg = value["messages"][0]
        from_number = msg["from"]
        
        # Handle text messages
        if msg["type"] == "text":
            message_text = msg["text"]["body"]
            
            result = process_farmer_query(
                message=message_text,
                farmer_id=from_number,
                channel="whatsapp",
                language="auto",
            )
            
            await send_whatsapp_message(from_number, result["response"])
        
        # Handle image messages (crop photos for diagnosis)
        elif msg["type"] == "image":
            image_id = msg["image"]["id"]
            caption = msg["image"].get("caption", "")
            
            # Download image from WhatsApp
            image_bytes = await download_whatsapp_media(image_id)
            
            if image_bytes:
                from agents.crop_doctor import diagnose_from_photo
                result = diagnose_from_photo(
                    image_bytes=image_bytes,
                    crop_name=extract_crop_from_caption(caption),
                    symptoms_description=caption,
                )
                await send_whatsapp_message(from_number, result["diagnosis"])
            else:
                await send_whatsapp_message(
                    from_number,
                    "I received your photo but couldn't process it. Please describe the symptoms in text."
                )
    
    except (KeyError, IndexError):
        pass
    
    return JSONResponse(content={"status": "ok"})


async def send_whatsapp_message(to: str, message: str):
    """Send WhatsApp message via Meta Cloud API."""
    async with httpx.AsyncClient() as http:
        await http.post(
            f"https://graph.facebook.com/v18.0/{os.environ.get('WHATSAPP_PHONE_ID')}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message},
            },
            headers={"Authorization": f"Bearer {os.environ.get('WHATSAPP_ACCESS_TOKEN')}"},
        )


async def download_whatsapp_media(media_id: str) -> bytes | None:
    """Download media file from WhatsApp."""
    async with httpx.AsyncClient() as http:
        meta_resp = await http.get(
            f"https://graph.facebook.com/v18.0/{media_id}",
            headers={"Authorization": f"Bearer {os.environ.get('WHATSAPP_ACCESS_TOKEN')}"},
        )
        url = meta_resp.json().get("url")
        if not url:
            return None
        
        media_resp = await http.get(
            url,
            headers={"Authorization": f"Bearer {os.environ.get('WHATSAPP_ACCESS_TOKEN')}"},
        )
        return media_resp.content


def extract_crop_from_caption(caption: str) -> str:
    """Simple crop name extraction from WhatsApp caption."""
    common_crops = ["maize", "corn", "beans", "coffee", "tea", "rice", "wheat",
                    "cassava", "potato", "tomato", "banana", "mango", "sorghum"]
    caption_lower = caption.lower()
    for crop in common_crops:
        if crop in caption_lower:
            return crop
    return "unknown crop"


# ─── HEALTH + INFO ───────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "AgriSense AI", "version": "1.0.0"}


@app.get("/api/info")
async def info():
    return {
        "name": "AgriSense AI",
        "description": "Multi-agent precision agriculture platform",
        "agents": ["mama-shamba-orchestrator", "crop-doctor", "weather", "market", "agronomy", "input-finder"],
        "channels": ["web", "sms", "whatsapp", "api"],
        "languages": ["en", "sw", "fr", "ha"],
        "platform": "DigitalOcean Gradient™ AI",
    }
