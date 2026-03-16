"""
AgriSense AI — Agronomy Agent
==============================
Provides soil, fertiliser, seed selection, and planting guidance.
Uses RAG from the agronomy knowledge base (DO Spaces + OpenSearch via Gradient AI).
"""

import os
from gradientai import GradientAI
from gradientai.adk import Agent, AgentConfig, function_tool, trace

client = GradientAI(api_key=os.environ["DIGITALOCEAN_API_TOKEN"])

AGRONOMY_INSTRUCTIONS = """
You are a certified agronomist specialising in smallholder farming systems 
across Sub-Saharan Africa, South Asia, and Latin America.

## Your expertise
- Soil health, pH correction, and nutrient management
- Fertiliser programmes (organic and inorganic)
- Seed variety selection for local conditions
- Crop spacing, planting depth, and population density
- Irrigation scheduling and water management
- Intercropping and companion planting
- Cover crops and soil regeneration

## Response format for fertiliser queries
Crop: [crop]
Field size: [farmer's field size]
Soil type: [if known]
Recommended fertiliser: [product name + quantity]
Application timing: [when and how]
Cost estimate: [realistic local estimate]
Organic alternative: [if available]

## Response format for soil queries
Current pH: [if provided]
Ideal pH for [crop]: [range]
Required amendment: [lime/sulfur + quantity per acre]
Other soil issues: [based on symptoms described]
Re-test in: [timeframe]

## Key principles
- Always prioritise locally available products
- Give quantities in units farmers understand (bags, tins, fistfuls per hole)
- Never recommend a programme without asking about field size first
- Mention that soil testing is the gold standard before heavy fertiliser investment
- Flag if inputs recommended are controlled/restricted

## Integrated approach
Always recommend integrated soil fertility management (ISFM):
combine small amounts of inorganic fertiliser with organic matter
for best results on degraded smallholder soils.
"""


@function_tool(
    description="Look up crop-specific fertiliser recommendations for a region",
    parameters={
        "crop": {"type": "string", "description": "Crop name"},
        "region": {"type": "string", "description": "Country and agroecological zone"},
        "field_size_acres": {"type": "number", "description": "Farm field size in acres"},
        "soil_ph": {"type": "number", "description": "Soil pH if known", "default": 0},
    }
)
def get_fertiliser_recommendations(
    crop: str,
    region: str,
    field_size_acres: float,
    soil_ph: float = 0,
) -> dict:
    """
    Calculate fertiliser requirements based on crop, region, and field size.
    In production, queries a crop nutrition database per agroecological zone.
    """

    # Fertiliser databases by crop (kg/ha of active nutrient)
    NUTRIENT_REQUIREMENTS = {
        "maize": {"N": 120, "P2O5": 60, "K2O": 60},
        "beans": {"N": 20, "P2O5": 40, "K2O": 40},   # Beans fix nitrogen
        "coffee": {"N": 180, "P2O5": 80, "K2O": 200},
        "rice": {"N": 90, "P2O5": 40, "K2O": 40},
        "wheat": {"N": 100, "P2O5": 50, "K2O": 30},
        "tomato": {"N": 150, "P2O5": 100, "K2O": 200},
        "potato": {"N": 120, "P2O5": 100, "K2O": 150},
        "cassava": {"N": 60, "P2O5": 30, "K2O": 80},
        "sorghum": {"N": 80, "P2O5": 40, "K2O": 30},
        "sunflower": {"N": 80, "P2O5": 50, "K2O": 80},
    }

    crop_lower = crop.lower()
    nutrients = NUTRIENT_REQUIREMENTS.get(crop_lower, {"N": 80, "P2O5": 40, "K2O": 40})

    # Convert field size: 1 acre = 0.405 ha
    ha = field_size_acres * 0.405

    # Calculate DAP (18-46-0) for phosphorus
    dap_kg = (nutrients["P2O5"] / 0.46) * ha
    dap_bags_50kg = round(dap_kg / 50, 1)

    # Calculate CAN (26% N) for nitrogen — subtract N from DAP
    n_from_dap = dap_kg * 0.18
    can_kg = max(0, ((nutrients["N"] - n_from_dap) / 0.26) * ha)
    can_bags_50kg = round(can_kg / 50, 1)

    # Lime recommendation for acidic soils
    lime_recommendation = None
    if soil_ph > 0 and soil_ph < 5.5:
        lime_kg_ha = (5.5 - soil_ph) * 2000  # Simplified buffer capacity
        lime_bags = round((lime_kg_ha * ha) / 50, 0)
        lime_recommendation = {
            "product": "Agricultural lime",
            "rate_kg_ha": round(lime_kg_ha),
            "bags_50kg": lime_bags,
            "timing": "Incorporate 4–6 weeks before planting",
            "note": "Re-test soil pH after 3 months",
        }

    return {
        "crop": crop,
        "field_size_acres": field_size_acres,
        "field_size_ha": round(ha, 2),
        "basal_fertiliser": {
            "product": "DAP (Di-Ammonium Phosphate 18-46-0)",
            "rate_kg_ha": round(nutrients["P2O5"] / 0.46),
            "total_kg": round(dap_kg),
            "bags_50kg": dap_bags_50kg,
            "timing": "Apply at planting, in furrow or hole",
        },
        "top_dressing": {
            "product": "CAN (Calcium Ammonium Nitrate, 26% N)",
            "rate_kg_ha": round(max(0, nutrients["N"] - n_from_dap) / 0.26),
            "total_kg": round(can_kg),
            "bags_50kg": can_bags_50kg,
            "timing": "Apply 4–6 weeks after germination when soil is moist",
        },
        "lime_recommendation": lime_recommendation,
        "organic_alternative": {
            "product": "Well-composted manure",
            "rate_tonnes_ha": 5,
            "total_tonnes": round(5 * ha, 1),
            "note": "Combine with 50% of inorganic rates for ISFM approach",
        },
    }


@function_tool(
    description="Get recommended seed varieties for a crop and region",
    parameters={
        "crop": {"type": "string", "description": "Crop name"},
        "region": {"type": "string", "description": "Country and region"},
        "priority": {
            "type": "string",
            "description": "Farmer priority: yield, drought_tolerance, disease_resistance, or market_preference",
        },
    }
)
def get_seed_varieties(crop: str, region: str, priority: str = "yield") -> dict:
    """
    Recommend certified seed varieties for a crop/region combination.
    Sourced from CGIAR, national seed authorities, and private breeders.
    """

    VARIETY_DATABASE = {
        "maize": {
            "yield": [
                {"name": "DK8031", "supplier": "Dekalb/Bayer", "yield_t_ha": 8.5, "maturity_days": 115, "notes": "Top performer in highland Kenya"},
                {"name": "H614D", "supplier": "Kenya Seed Company", "yield_t_ha": 7.8, "maturity_days": 120, "notes": "Popular in Rift Valley"},
                {"name": "SEEDCO SC403", "supplier": "SeedCo", "yield_t_ha": 7.2, "maturity_days": 110, "notes": "MLN-tolerant, East Africa"},
            ],
            "drought_tolerance": [
                {"name": "WEMA DTMA", "supplier": "Kenya Seed Company", "yield_t_ha": 5.5, "maturity_days": 90, "notes": "Water-efficient, ASALs"},
                {"name": "DT Hybrid", "supplier": "CIMMYT partners", "yield_t_ha": 5.0, "maturity_days": 85, "notes": "Bred for drought stress"},
            ],
            "disease_resistance": [
                {"name": "SEEDCO SC403", "supplier": "SeedCo", "yield_t_ha": 7.2, "maturity_days": 110, "notes": "MLN + GLS resistant"},
                {"name": "PHB 3253", "supplier": "Pioneer", "yield_t_ha": 7.5, "maturity_days": 112, "notes": "Turcicum blight resistant"},
            ],
        },
        "beans": {
            "yield": [
                {"name": "Lyamungu 85", "supplier": "TARI Tanzania", "yield_t_ha": 2.1, "maturity_days": 75, "notes": "High-yielding climbing bean"},
                {"name": "KK8", "supplier": "Kenya Seed Company", "yield_t_ha": 1.8, "maturity_days": 70, "notes": "Bush bean, popular in western Kenya"},
            ],
            "disease_resistance": [
                {"name": "TARS-HT1", "supplier": "USAID/Bean program", "yield_t_ha": 1.6, "maturity_days": 65, "notes": "Rust and bean fly resistant"},
            ],
        },
        "tomato": {
            "yield": [
                {"name": "Kilele F1", "supplier": "Syngenta", "yield_t_ha": 80, "maturity_days": 75, "notes": "Determinate, excellent shelf life"},
                {"name": "Shanty F1", "supplier": "Sakata", "yield_t_ha": 75, "maturity_days": 70, "notes": "Very popular in East Africa"},
            ],
            "disease_resistance": [
                {"name": "TYLCV-resistant F1", "supplier": "Various", "yield_t_ha": 60, "maturity_days": 75, "notes": "Tomato yellow leaf curl virus resistant"},
            ],
        },
    }

    crop_lower = crop.lower()
    varieties = VARIETY_DATABASE.get(crop_lower, {}).get(priority, [])

    if not varieties:
        varieties = VARIETY_DATABASE.get(crop_lower, {}).get("yield", [])

    return {
        "crop": crop,
        "region": region,
        "priority": priority,
        "recommended_varieties": varieties[:3],
        "where_to_buy": "Visit an AGRA-certified or government-accredited agro-dealer. Always buy in original sealed packaging.",
        "seed_rate_kg_ha": {
            "maize": 25, "beans": 60, "tomato": 0.25,
            "wheat": 120, "sorghum": 10, "rice": 80,
        }.get(crop_lower, 30),
    }


@trace
def build_agronomy_agent() -> Agent:
    """Build the Agronomy specialist agent with RAG + function tools."""

    config = AgentConfig(
        name="agrisense-agronomy",
        model="claude-sonnet-4-6",
        instructions=AGRONOMY_INSTRUCTIONS,

        # RAG from agronomy guides
        knowledge_base_ids=[
            os.environ.get("AGRONOMY_KB_ID"),
        ],

        retrieval_config={
            "top_k": 4,
            "min_relevance_score": 0.60,
            "chunking_strategy": "section_based",
        },

        # Function tools
        function_routes=[
            {
                "function": get_fertiliser_recommendations,
                "description": "Calculate fertiliser quantities for a crop and field size",
            },
            {
                "function": get_seed_varieties,
                "description": "Get recommended certified seed varieties for a crop and region",
            },
        ],

        guardrails=["content-moderation", "sensitive-data"],

        max_tokens=900,
        temperature=0.25,
    )

    return Agent(config=config, client=client)
