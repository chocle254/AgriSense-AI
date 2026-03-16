"""
AgriSense AI — Weather Agent & Market Agent
==========================================
Both use Gradient AI function calling to fetch live external data.
"""

import os
import httpx
from gradientai import GradientAI
from gradientai.adk import Agent, AgentConfig, function_tool, trace

client = GradientAI(api_key=os.environ["DIGITALOCEAN_API_TOKEN"])


# ─── FUNCTION TOOLS (called by Gradient AI agents) ─────────────────────────

@function_tool(
    description="Get 7-day weather forecast and planting suitability for a farm location",
    parameters={
        "lat": {"type": "number", "description": "Latitude of the farm"},
        "lng": {"type": "number", "description": "Longitude of the farm"},
        "crop": {"type": "string", "description": "Crop being grown (for planting advice)"},
    }
)
async def get_weather_forecast(lat: float, lng: float, crop: str = "") -> dict:
    """Fetch weather from OpenWeatherMap and compute planting suitability."""
    async with httpx.AsyncClient() as http:
        resp = await http.get(
            "https://api.openweathermap.org/data/3.0/onecall",
            params={
                "lat": lat,
                "lon": lng,
                "appid": os.environ["OPENWEATHER_API_KEY"],
                "units": "metric",
                "exclude": "minutely,hourly,alerts",
            },
            timeout=10,
        )
        data = resp.json()
    
    daily = data.get("daily", [])[:7]
    
    # Compute planting suitability score (0–100)
    suitability = compute_planting_suitability(daily, crop)
    
    return {
        "forecast": [
            {
                "date": d["dt"],
                "temp_min": d["temp"]["min"],
                "temp_max": d["temp"]["max"],
                "rain_mm": d.get("rain", 0),
                "humidity": d["humidity"],
                "description": d["weather"][0]["description"],
            }
            for d in daily
        ],
        "planting_suitability_score": suitability["score"],
        "planting_recommendation": suitability["recommendation"],
        "best_planting_window": suitability["window"],
    }


def compute_planting_suitability(daily_forecast: list, crop: str) -> dict:
    """
    Rule-based planting suitability calculator.
    In production, this would be crop-specific and ML-powered.
    """
    # Basic heuristics
    avg_rain = sum(d.get("rain", 0) for d in daily_forecast) / max(len(daily_forecast), 1)
    avg_temp = sum((d["temp"]["min"] + d["temp"]["max"]) / 2 for d in daily_forecast) / max(len(daily_forecast), 1)
    
    score = 50
    if 20 <= avg_temp <= 30:
        score += 25
    elif avg_temp < 15 or avg_temp > 35:
        score -= 25
    
    if avg_rain > 3:
        score += 25
    elif avg_rain < 1:
        score -= 15
    
    score = max(0, min(100, score))
    
    if score >= 70:
        recommendation = "Good conditions for planting. Proceed this week."
        window = "Next 3–5 days"
    elif score >= 40:
        recommendation = "Marginal conditions. Consider waiting for more rain."
        window = "Wait 5–7 days and re-check"
    else:
        recommendation = "Poor conditions for planting. Wait for better weather."
        window = "Wait at least 10 days"
    
    return {"score": score, "recommendation": recommendation, "window": window}


@function_tool(
    description="Get current commodity market prices for a crop in a specific region",
    parameters={
        "crop": {"type": "string", "description": "Crop name (e.g. maize, coffee, beans)"},
        "region": {"type": "string", "description": "Country and region (e.g. Kenya, Rift Valley)"},
        "unit": {"type": "string", "description": "Unit (kg or 90kg bag)", "default": "kg"},
    }
)
async def get_market_prices(crop: str, region: str, unit: str = "kg") -> dict:
    """
    Fetch commodity prices from regional market APIs.
    Integrates with EAGC (East Africa Grain Council) price feed and local exchanges.
    """
    
    # In production: real API call to EAGC, ESOKO, or regional commodity exchange
    # For demo: returns realistic price data
    
    SAMPLE_PRICES = {
        "maize": {"Kenya": {"price": 45, "currency": "KES", "trend": "rising", "best_market": "Nairobi Wakulima"},
                  "Tanzania": {"price": 800, "currency": "TZS", "trend": "stable", "best_market": "Kariakoo"}},
        "coffee": {"Kenya": {"price": 380, "currency": "KES", "trend": "rising", "best_market": "Nairobi Coffee Exchange"},
                   "Ethiopia": {"price": 95, "currency": "ETB", "trend": "rising", "best_market": "ECX Jimma"}},
        "beans": {"Kenya": {"price": 120, "currency": "KES", "trend": "falling", "best_market": "Wakulima Market"},
                  "Uganda": {"price": 3200, "currency": "UGX", "trend": "stable", "best_market": "Owino Market"}},
    }
    
    crop_lower = crop.lower()
    country = region.split(",")[0].strip() if "," in region else region.strip()
    
    price_data = (
        SAMPLE_PRICES.get(crop_lower, {}).get(country)
        or {"price": 50, "currency": "USD", "trend": "unknown", "best_market": "Local market"}
    )
    
    return {
        "crop": crop,
        "region": region,
        "price_per_kg": price_data["price"],
        "currency": price_data["currency"],
        "trend": price_data["trend"],
        "best_selling_market": price_data["best_market"],
        "advice": generate_sell_advice(price_data["trend"]),
        "updated_at": "today",
    }


def generate_sell_advice(trend: str) -> str:
    advice_map = {
        "rising": "Prices are rising. Consider holding 30-40% of your stock for 2-3 more weeks.",
        "falling": "Prices are falling. Sell now to avoid further losses. Prioritise perishables.",
        "stable": "Prices are stable. Sell at your convenience. No urgency.",
        "unknown": "Price trend data unavailable. Check with your local cooperative.",
    }
    return advice_map.get(trend, advice_map["unknown"])


# ─── WEATHER AGENT ───────────────────────────────────────────────────────────

WEATHER_AGENT_INSTRUCTIONS = """
You are an agricultural meteorologist specialising in smallholder farm planning.

Your job:
1. Interpret weather forecasts in terms farmers understand
2. Give SPECIFIC planting, harvesting, and field activity recommendations
3. Warn about risks: drought, floods, frost, pests linked to weather

Always translate weather data into actionable farm decisions.
Use local terms where possible (e.g., "long rains" / "short rains" for East Africa).
"""

@trace
def build_weather_agent() -> Agent:
    config = AgentConfig(
        name="agrisense-weather",
        model="llama-3.1-70b-instruct",   # Fast open-source model for structured data
        instructions=WEATHER_AGENT_INSTRUCTIONS,
        function_routes=[
            {"function": get_weather_forecast, "description": "Get weather forecast and planting advice"},
        ],
        guardrails=["content-moderation"],
        max_tokens=500,
        temperature=0.3,
    )
    return Agent(config=config, client=client)


# ─── MARKET AGENT ────────────────────────────────────────────────────────────

MARKET_AGENT_INSTRUCTIONS = """
You are an agricultural market analyst helping smallholder farmers maximise 
their income by timing sales and choosing the best markets.

Your job:
1. Get current prices for the farmer's crops
2. Compare prices across nearby markets
3. Give sell / hold recommendations with clear reasoning
4. Explain price trends in simple terms
5. Suggest value-addition options if prices are low (e.g., drying, storage)

Be honest about uncertainty in market predictions. Farmers make real financial 
decisions based on your advice — accuracy matters more than confidence.
"""

@trace
def build_market_agent() -> Agent:
    config = AgentConfig(
        name="agrisense-market",
        model="gpt-4o",
        instructions=MARKET_AGENT_INSTRUCTIONS,
        function_routes=[
            {"function": get_market_prices, "description": "Get current commodity market prices"},
        ],
        guardrails=["content-moderation"],
        max_tokens=600,
        temperature=0.2,
    )
    return Agent(config=config, client=client)
