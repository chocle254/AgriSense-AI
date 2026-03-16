"""
AgriSense AI — Crop Doctor Agent
==================================
Specialist agent for crop disease and pest diagnosis.
Uses Gradient AI knowledge base (RAG) with 2,000+ disease entries.
Supports image-based diagnosis via GPT-4o vision on serverless inference.
"""

import os
import base64
from gradientai import GradientAI
from gradientai.adk import Agent, AgentConfig, trace

client = GradientAI(api_key=os.environ["DIGITALOCEAN_API_TOKEN"])

CROP_DOCTOR_INSTRUCTIONS = """
You are an expert plant pathologist and crop protection specialist.
You diagnose crop diseases and pest infestations with precision.

## Diagnosis process
1. IDENTIFY the crop first (ask if unclear)
2. Ask about SYMPTOMS: color changes, texture, location on plant, spread pattern
3. Ask about CONDITIONS: recent weather, soil type, neighboring farms affected
4. Provide DIAGNOSIS with confidence level (High/Medium/Low)
5. Give TREATMENT: organic options first, then conventional if needed
6. Give PREVENTION: how to stop it next season
7. Give URGENCY: "Act today" / "Act this week" / "Monitor for 3 days"

## Format for diagnosis
Crop: [crop name]
Likely problem: [disease/pest name]
Confidence: [High/Medium/Low]
Treatment: [specific steps]
Prevention: [next season tips]
Urgency: [timeframe]

## Knowledge base
You have access to a knowledge base of 2,000+ crop diseases, pests, and 
nutrient deficiencies covering crops grown in Sub-Saharan Africa, South Asia, 
and Latin America. Always retrieve from knowledge base before answering.

## Important
- NEVER recommend a pesticide without also giving protective equipment instructions
- If you suspect Fall Armyworm, Wheat Stem Rust, or Cassava Mosaic — 
  escalate to "ALERT: Notify your local agriculture extension officer immediately"
- Always mention whether a treatment is available at local agro-dealers
"""

@trace
def build_crop_doctor_agent() -> Agent:
    """Build the Crop Doctor specialist agent with RAG knowledge base."""
    
    config = AgentConfig(
        name="agrisense-crop-doctor",
        # Use GPT-4o for vision capability (crop photo analysis)
        model="gpt-4o",
        instructions=CROP_DOCTOR_INSTRUCTIONS,
        
        # Gradient AI knowledge base — disease database
        knowledge_base_ids=[
            os.environ.get("CROP_DISEASES_KB_ID"),    # 2000+ disease entries
        ],
        
        # RAG retrieval settings
        retrieval_config={
            "top_k": 5,
            "min_relevance_score": 0.65,
            "chunking_strategy": "semantic",
        },
        
        guardrails=["content-moderation", "sensitive-data"],
        
        max_tokens=800,
        temperature=0.2,   # Very low temp for medical/diagnostic accuracy
    )
    
    return Agent(config=config, client=client)


@trace
def diagnose_from_photo(
    image_bytes: bytes,
    crop_name: str,
    symptoms_description: str,
    location: dict | None = None,
) -> dict:
    """
    Diagnose crop disease from a photo using GPT-4o vision.
    
    The image is processed by GPT-4o via Gradient AI serverless inference,
    then the diagnosis is enriched with RAG from the disease knowledge base.
    """
    
    # Encode image for vision model
    image_b64 = base64.b64encode(image_bytes).decode()
    
    agent = build_crop_doctor_agent()
    
    vision_prompt = f"""
Analyze this crop photo for disease or pest damage.
Crop: {crop_name}
Farmer describes: {symptoms_description}
Location/Region: {location.get("region", "unknown") if location else "unknown"}

Provide a structured diagnosis following your diagnosis protocol.
"""
    
    response = agent.chat_with_image(
        message=vision_prompt,
        image_base64=image_b64,
        image_media_type="image/jpeg",
    )
    
    return {
        "diagnosis": response.text,
        "rag_sources": response.metadata.get("rag_sources", []),
        "confidence": extract_confidence(response.text),
        "urgency": extract_urgency(response.text),
        "trace_id": response.trace_id,
    }


def extract_confidence(text: str) -> str:
    """Extract confidence level from diagnosis text."""
    text_lower = text.lower()
    if "confidence: high" in text_lower:
        return "HIGH"
    elif "confidence: medium" in text_lower:
        return "MEDIUM"
    return "LOW"


def extract_urgency(text: str) -> str:
    """Extract urgency from diagnosis text."""
    text_lower = text.lower()
    if "act today" in text_lower or "alert:" in text_lower:
        return "URGENT"
    elif "act this week" in text_lower:
        return "HIGH"
    return "MONITOR"
