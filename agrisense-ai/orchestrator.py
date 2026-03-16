"""
AgriSense AI — Orchestrator Agent "Mama Shamba"
================================================
Built on DigitalOcean Gradient™ AI Platform using the Agent Development Kit (ADK).
Uses Gradient AI's native multi-agent routing to dispatch queries to specialist agents.
"""

import os
from gradientai import GradientAI
from gradientai.adk import Agent, trace, AgentConfig

client = GradientAI(api_key=os.environ["DIGITALOCEAN_API_TOKEN"])

MAMA_SHAMBA_INSTRUCTIONS = """
You are Mama Shamba — a warm, experienced, and deeply knowledgeable farming 
companion serving smallholder farmers across Africa and the developing world.

Your name means "Mother of the Farm" in Kiswahili. You speak with the authority 
of a seasoned agronomist and the warmth of a trusted community elder.

## Your purpose
Help farmers grow more, earn more, and waste less — in their language, 
on the device they have.

## Language
Always respond in the SAME language the farmer uses. If they write in Kiswahili, 
respond in Kiswahili. If French, respond in French. English is your fallback.

## Routing rules (internal — do not mention to farmer)
Route to specialist agents based on query type:
- "my maize has yellow spots / disease / pest / sick plant" → crop_doctor_agent
- "when should I plant / will it rain / weather / forecast" → weather_agent  
- "price of maize / sell my harvest / market / best price" → market_agent
- "how much fertiliser / soil test / which seed / planting guide" → agronomy_agent
- "where to buy inputs / find seed dealer / agro-dealer" → input_finder_agent

## Tone
- Warm and encouraging — farming is hard, acknowledge the farmer's effort
- Practical — give actionable advice, not theory
- Concise for SMS (under 160 chars when channel=sms), fuller for web/WhatsApp
- Never condescending — these farmers know their land

## When you don't know
Say so honestly, and recommend they contact their local extension officer.
Never fabricate data.

## Safety
Do not recommend restricted pesticides or dangerous chemicals without clear 
safety instructions. Always mention protective equipment.
"""

@trace
def build_orchestrator_agent() -> Agent:
    """Build and return the Mama Shamba orchestrator agent."""
    
    config = AgentConfig(
        name="mama-shamba-orchestrator",
        model="claude-sonnet-4-6",   # Claude Sonnet 4.6 via Gradient AI serverless inference
        instructions=MAMA_SHAMBA_INSTRUCTIONS,
        
        # Gradient AI guardrails
        guardrails=[
            "content-moderation",
            "jailbreak",
            "sensitive-data",
        ],
        
        # Multi-agent routes — Gradient AI native routing
        agent_routes=[
            {
                "name": "crop_doctor_agent",
                "condition": "Query involves crop disease, pest, yellowing, wilting, spots, insects, or plant health",
                "agent_id": os.environ.get("CROP_DOCTOR_AGENT_ID"),
            },
            {
                "name": "weather_agent",
                "condition": "Query involves weather, rainfall, planting timing, frost, or seasonal forecasts",
                "agent_id": os.environ.get("WEATHER_AGENT_ID"),
            },
            {
                "name": "market_agent",
                "condition": "Query involves crop prices, where to sell, market rates, or commodity values",
                "agent_id": os.environ.get("MARKET_AGENT_ID"),
            },
            {
                "name": "agronomy_agent",
                "condition": "Query involves fertiliser, soil, seeds, planting depth, irrigation, or agronomy",
                "agent_id": os.environ.get("AGRONOMY_AGENT_ID"),
            },
            {
                "name": "input_finder_agent",
                "condition": "Query involves finding a shop, buying inputs, agro-dealer location, or suppliers",
                "agent_id": os.environ.get("INPUT_FINDER_AGENT_ID"),
            },
        ],
        
        max_tokens=1024,
        temperature=0.3,   # Lower temp for more consistent, factual agricultural advice
    )
    
    return Agent(config=config, client=client)


@trace
def process_farmer_query(
    message: str,
    farmer_id: str,
    channel: str = "web",         # "web" | "sms" | "whatsapp"
    language: str = "auto",       # auto-detect or force language
    location: dict | None = None, # {"lat": float, "lng": float, "region": str}
    conversation_history: list | None = None,
) -> dict:
    """
    Process a farmer's query through the Mama Shamba orchestrator.
    
    Returns:
        {
            "response": str,           # Agent's response text
            "agent_used": str,         # Which specialist handled it
            "language_detected": str,  # Language of response
            "sources": list,           # RAG sources used (if any)
            "trace_id": str,           # For observability
        }
    """
    agent = build_orchestrator_agent()
    
    # Enrich context with channel and location info
    system_context = f"""
Channel: {channel}
{"Keep response under 160 characters for SMS." if channel == "sms" else ""}
{"Format response for WhatsApp (use *bold* and line breaks)." if channel == "whatsapp" else ""}
Location context: {location or "unknown"}
Farmer ID: {farmer_id}
"""
    
    history = conversation_history or []
    
    response = agent.chat(
        message=message,
        system_context=system_context,
        conversation_history=history,
    )
    
    return {
        "response": response.text,
        "agent_used": response.metadata.get("routed_to", "orchestrator"),
        "language_detected": response.metadata.get("language", "en"),
        "sources": response.metadata.get("rag_sources", []),
        "trace_id": response.trace_id,
    }
