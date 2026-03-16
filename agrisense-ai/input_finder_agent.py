"""
AgriSense AI — Input Finder Agent
===================================
Helps farmers find certified agro-dealers, seed stockists, and
fertiliser suppliers near them using geo-indexed knowledge base + maps API.
"""

import os
import math
import httpx
from gradientai import GradientAI
from gradientai.adk import Agent, AgentConfig, function_tool, trace

client = GradientAI(api_key=os.environ["DIGITALOCEAN_API_TOKEN"])

INPUT_FINDER_INSTRUCTIONS = """
You are a supply chain specialist helping smallholder farmers find trusted,
certified input suppliers near their farms.

## Your job
1. Find agro-dealers within a reasonable distance (start with 10km, extend to 30km if sparse)
2. Prioritise CERTIFIED dealers (AGRA, government-accredited, or cooperative-affiliated)
3. Check if they stock the specific product the farmer needs
4. Give practical directions where possible (road names, landmarks — GPS not everyone has)
5. Mention if the dealer has recently been reported as out-of-stock for that product

## Always warn about
- Counterfeit seeds and fertilisers (a real risk in rural Africa)
- Buying only in ORIGINAL SEALED packaging from certified dealers
- Avoiding roadside vendors for certified seed — quality not guaranteed
- Price gouging — quote regional fair price if known

## Format
Dealer: [name]
Distance: [km/miles]
Products: [what they stock]
Phone: [if available]
Directions: [simple landmarks]
Certified: [Yes/No]
Note: [any flags]

## If no dealer found within 30km
- Recommend the nearest market town
- Suggest the farmer's cooperative bulk-ordering service
- Mention any mobile agro-dealer programmes in the region (e.g. One Acre Fund, AFA)
"""


@function_tool(
    description="Find agro-dealers and input suppliers near a GPS location",
    parameters={
        "lat": {"type": "number", "description": "Farmer's latitude"},
        "lng": {"type": "number", "description": "Farmer's longitude"},
        "product": {"type": "string", "description": "Input needed (e.g. maize seed, DAP, pesticide name)"},
        "radius_km": {"type": "number", "description": "Search radius in kilometers", "default": 20},
    }
)
async def find_nearby_dealers(
    lat: float,
    lng: float,
    product: str,
    radius_km: float = 20,
) -> dict:
    """
    Search for verified agro-dealers near the farmer's location.
    In production, queries the supplier knowledge base indexed in DO OpenSearch.
    """

    # Production: query Gradient AI supplier knowledge base with geo-filter
    # Demo: return realistic sample data based on coordinates

    # Kenya / East Africa region sample
    SAMPLE_DEALERS = [
        {
            "name": "Eldoret Agrovet",
            "lat": lat + 0.05,
            "lng": lng + 0.03,
            "products": ["maize seed", "DAP", "CAN", "herbicides", "fungicides"],
            "phone": "+254 712 345 678",
            "certified": True,
            "certifier": "KEPHIS",
            "directions": "On Eldoret-Kitale Road, near Khetia's Supermarket",
            "hours": "Mon–Sat 8am–6pm",
        },
        {
            "name": "Agri-Supply Kenya Ltd",
            "lat": lat - 0.08,
            "lng": lng + 0.06,
            "products": ["certified seed", "fertilisers", "irrigation equipment", "sprayers"],
            "phone": "+254 722 456 789",
            "certified": True,
            "certifier": "AGRA",
            "directions": "Town centre, opposite the post office",
            "hours": "Mon–Fri 8am–5:30pm, Sat 9am–1pm",
        },
        {
            "name": "Kamau Agrovet",
            "lat": lat + 0.15,
            "lng": lng - 0.10,
            "products": ["seeds", "pesticides", "animal feed"],
            "phone": "+254 733 567 890",
            "certified": False,
            "certifier": None,
            "directions": "Near the secondary school, Nandi Road",
            "hours": "Daily 7am–7pm",
        },
    ]

    def haversine_km(lat1, lng1, lat2, lng2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1))
             * math.cos(math.radians(lat2))
             * math.sin(dlng / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))

    product_lower = product.lower()

    results = []
    for dealer in SAMPLE_DEALERS:
        dist = haversine_km(lat, lng, dealer["lat"], dealer["lng"])
        if dist > radius_km:
            continue

        # Check if dealer stocks the requested product
        stocks_product = any(
            product_lower in p.lower() or p.lower() in product_lower
            for p in dealer["products"]
        )

        results.append({
            "name": dealer["name"],
            "distance_km": round(dist, 1),
            "phone": dealer["phone"],
            "certified": dealer["certified"],
            "certifier": dealer["certifier"],
            "stocks_requested_product": stocks_product,
            "all_products": dealer["products"],
            "directions": dealer["directions"],
            "hours": dealer["hours"],
        })

    results.sort(key=lambda x: (-x["certified"], x["distance_km"]))

    return {
        "search_location": {"lat": lat, "lng": lng},
        "product_requested": product,
        "radius_km": radius_km,
        "dealers_found": len(results),
        "results": results,
        "safety_note": (
            "Always buy seeds and agrochemicals in ORIGINAL SEALED packaging "
            "from certified dealers. Counterfeit products are common — "
            "if the price seems too low, be suspicious."
        ),
    }


@function_tool(
    description="Get fair market prices for agricultural inputs to avoid overcharging",
    parameters={
        "product": {"type": "string", "description": "Input product (e.g. 50kg DAP, 2kg maize seed)"},
        "country": {"type": "string", "description": "Country name"},
    }
)
def get_input_fair_price(product: str, country: str) -> dict:
    """
    Reference prices for agricultural inputs to protect farmers from price gouging.
    """

    FAIR_PRICES = {
        "DAP": {
            "Kenya": {"price_range": "5,200–5,800", "currency": "KES", "unit": "50kg bag"},
            "Tanzania": {"price_range": "110,000–130,000", "currency": "TZS", "unit": "50kg bag"},
            "Uganda": {"price_range": "135,000–150,000", "currency": "UGX", "unit": "50kg bag"},
        },
        "CAN": {
            "Kenya": {"price_range": "3,800–4,400", "currency": "KES", "unit": "50kg bag"},
            "Tanzania": {"price_range": "85,000–100,000", "currency": "TZS", "unit": "50kg bag"},
        },
        "maize seed": {
            "Kenya": {"price_range": "650–900", "currency": "KES", "unit": "2kg pack"},
            "Tanzania": {"price_range": "12,000–18,000", "currency": "TZS", "unit": "2kg pack"},
        },
    }

    product_lower = product.lower()
    country_clean = country.strip()

    for key, countries in FAIR_PRICES.items():
        if key in product_lower:
            price_info = countries.get(country_clean)
            if price_info:
                return {
                    "product": product,
                    "country": country,
                    "fair_price_range": price_info["price_range"],
                    "currency": price_info["currency"],
                    "unit": price_info["unit"],
                    "note": "Prices above this range — negotiate or try another dealer. Government-subsidised programmes may offer lower prices.",
                }

    return {
        "product": product,
        "country": country,
        "fair_price_range": "Check with local cooperative or ministry of agriculture",
        "note": "Price data unavailable for this product. Contact your extension officer for guidance.",
    }


@trace
def build_input_finder_agent() -> Agent:
    """Build the Input Finder agent with geo-search and supplier KB."""

    config = AgentConfig(
        name="agrisense-input-finder",
        model="llama-3.1-70b-instruct",
        instructions=INPUT_FINDER_INSTRUCTIONS,

        knowledge_base_ids=[
            os.environ.get("SUPPLIER_KB_ID"),
        ],

        retrieval_config={
            "top_k": 6,
            "min_relevance_score": 0.55,
        },

        function_routes=[
            {
                "function": find_nearby_dealers,
                "description": "Find agro-dealers near a GPS location",
            },
            {
                "function": get_input_fair_price,
                "description": "Get fair reference prices for agricultural inputs",
            },
        ],

        guardrails=["content-moderation"],

        max_tokens=700,
        temperature=0.3,
    )

    return Agent(config=config, client=client)
