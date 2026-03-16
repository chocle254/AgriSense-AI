# AgriSense AI — Devpost Project Description

## Inspiration

Africa has 33 million smallholder farmers. Each of them makes dozens of critical decisions every season — when to plant, which seed to buy, how much fertiliser to use, whether that yellowing on their maize is nitrogen deficiency or Fall Armyworm, and whether to sell their harvest now or wait three weeks for prices to rise.

For most of these farmers, the only expert they can consult is an agricultural extension officer — and there is roughly **one extension officer per 2,500 farmers** in Sub-Saharan Africa. The result is 25–40% of harvests lost every year to preventable diseases, bad timing, and poor input choices.

We built AgriSense AI because a farmer in Eldoret, Kenya deserves the same quality of agronomic advice as a commercial farm in Iowa — and they need it in Kiswahili, on the phone they already have, at a price they can afford (free).

---

## What it does

AgriSense AI is a **multi-agent precision agriculture platform** built on DigitalOcean Gradient™ AI. It puts a team of specialist AI agents in every farmer's pocket:

**🌾 Mama Shamba** (the orchestrator) is a warm, multilingual farming companion who listens to the farmer's query in English, Kiswahili, French, or Hausa, understands the intent, and routes the request to the right specialist.

**🔬 Crop Doctor** diagnoses crop diseases and pest infestations from text descriptions or photos. Upload a photo of your sick maize on WhatsApp and get a diagnosis with treatment plan within seconds.

**🌤 Weather Agent** interprets weather forecasts into concrete planting decisions: "Don't plant this week — there's a dry spell coming. Plant Tuesday of next week when the rains resume."

**📊 Market Agent** tracks commodity prices across regional markets and tells farmers whether to sell now or hold — with the reasoning explained plainly.

**🌱 Agronomy Agent** calculates exactly how many bags of fertiliser a farmer needs for their specific field size, recommends certified seed varieties for their agroecological zone, and answers soil management questions.

**🏪 Input Finder** locates certified agro-dealers within 20–30km, checks if they stock the product needed, and warns about fair price ranges to prevent gouging.

Farmers can access all of this via:
- A web app on any smartphone
- **SMS / USSD** via Africa's Talking — no data needed, works on a basic phone from any of 35 African countries
- **WhatsApp** — where 500M Africans already communicate daily
- REST API — for NGO and government system integrations

---

## How we built it

AgriSense AI uses the complete DigitalOcean Gradient™ AI stack:

### 1. Multi-Agent Routing
The Mama Shamba orchestrator is built with Gradient AI's native multi-agent routing. We define five specialist agents and describe the conditions under which each should handle a query. Gradient AI handles all the routing logic — no custom NLU or intent classification code required.

### 2. Knowledge Bases (RAG)
Three knowledge bases power the agents:
- **Crop Diseases KB** — 2,000+ disease/pest/deficiency entries with symptoms, treatments, and severity levels. Stored in DigitalOcean Spaces, indexed with Gradient AI's semantic chunking strategy for maximum retrieval accuracy.
- **Agronomy Guides KB** — Regional planting guides, fertiliser recommendations, and soil management documents from CGIAR, national agricultural ministries, and AGRA.
- **Supplier Directory KB** — Geo-indexed database of verified agro-dealers across East and West Africa.

### 3. Serverless Inference
We use three models via Gradient AI serverless inference:
- **Claude Sonnet 4.6** — orchestration, complex reasoning, multi-turn agronomy conversations
- **Llama 3.1 70B** — fast structured responses for weather and market data queries
- **GPT-4o** — crop disease photo analysis via vision capability

### 4. Function Calling
Live external data flows through four function tools registered with the agents:
- `get_weather_forecast` → OpenWeatherMap API with planting suitability scoring
- `get_market_prices` → regional commodity exchange feeds (EAGC, ESOKO)
- `find_nearby_dealers` → geo-search against supplier knowledge base
- `get_fertiliser_recommendations` → crop nutrition database with bag quantity calculations

### 5. Guardrails
Content moderation and jailbreak guardrails on all agents prevent misuse. Sensitive data guardrails strip PII before logging. We added an agriculture-specific guardrail layer: restricted pesticides always include safety equipment instructions, and critical disease detections (Fall Armyworm, MLN) trigger an escalation path to extension services.

### 6. Agent Evaluations
We built a 150-question evaluation dataset across crop disease, agronomy, market, and multilingual categories. The evaluation pipeline runs automatically on every deployment via `gradient agent evaluate`, blocking deploys if correctness drops below 85%.

### 7. Tracing & Observability
Full agent trace capture lets us audit every farming conversation for quality, debug edge cases, and measure which agents handle the most queries — informing what knowledge to expand next.

### 8. Agent Development Kit (ADK)
The entire development workflow uses the Gradient ADK: local hot-reload for testing, agent version management, and one-command production deployment.

---

## Challenges we ran into

**Multilingual agricultural vocabulary** is harder than general multilingual NLP. Kiswahili terms for crop diseases don't always have direct translations — farmers use vernacular names for pests that differ village by village. We invested heavily in the knowledge base chunking strategy and retrieval tuning to surface relevant content even from colloquial queries.

**SMS constraints** forced us to build response length logic at the orchestrator level. A Llama 3.1 response that's perfect for web needs to be distilled to 155 characters for SMS — without losing the actionable core. We implemented channel-aware prompting and truncation with semantic sentence boundary detection.

**Trust calibration** matters enormously in agriculture. Farmers make real financial decisions based on AI advice. We set lower temperatures on all diagnostic agents (0.2), enforce knowledge base retrieval before any disease diagnosis, and built explicit confidence levels into every diagnosis output. We deliberately avoid false certainty.

---

## Accomplishments we're proud of

- **Zero-code multi-agent routing** — Gradient AI's native routing replaced what would have been hundreds of lines of custom intent classification
- **Full channel coverage** — the same agent backend handles web, SMS, and WhatsApp with channel-appropriate formatting
- **Language detection + response** — Mama Shamba detects query language and responds in kind with zero additional configuration
- **Photo diagnosis on WhatsApp** — farmers can send a crop photo via WhatsApp and receive a structured diagnosis in under 10 seconds

---

## What we learned

DigitalOcean Gradient AI dramatically reduces the time from idea to deployed, production-ready multi-agent system. The knowledge base setup with DO Spaces integration took less than an hour. Agent routing that would have taken a week to build custom was configured in a YAML file.

The biggest learning: **the bottleneck in agricultural AI isn't the model — it's the data**. Building a high-quality, regionally accurate knowledge base of crop diseases and agronomy recommendations was where most of our effort went. The AI platform itself got out of the way and let us focus on that.

---

## What's next

- **Soil test interpretation** — farmers photograph their soil test results and get a personalised fertiliser programme
- **Crop insurance integration** — automatically document disease outbreaks with timestamps and photos for insurance claims
- **Community intelligence** — aggregate anonymised disease reports to create early warning maps (Fall Armyworm spreading north through the Rift Valley)
- **Voice interface** — IVR phone integration for farmers who can't read
- **Offline-first mobile app** — cached disease database and basic diagnosis available without connectivity

---

## Built with

**DigitalOcean Gradient™ AI Platform:**
- Multi-Agent Routing
- Knowledge Bases (RAG) with Semantic Chunking
- Serverless Inference (Claude Sonnet 4.6, GPT-4o, Llama 3.1 70B)
- Function Calling / Function Tools
- Agent Guardrails (Content Moderation, Jailbreak, Sensitive Data)
- Agent Evaluations
- Agent Tracing & Observability
- Agent Development Kit (ADK)

**DigitalOcean Infrastructure:**
- DO App Platform (backend + frontend deployment)
- DO Spaces (knowledge base document storage)
- GPU Droplets (vision model backup hosting)

**Other Technologies:**
- Python / FastAPI (backend)
- React / Vite (frontend)
- Africa's Talking API (SMS/USSD)
- Meta Cloud API (WhatsApp Business)
- OpenWeatherMap API (weather data)

---

## Try it

**Live demo:** https://agrisense.yourdomain.com  
**SMS:** Text `HELP` to our Africa's Talking shortcode  
**WhatsApp:** +254 700 000 000  
**GitHub:** https://github.com/yourusername/agrisense-ai  

Sample queries to try:
- "My maize leaves are yellow from the tips — what's wrong?"
- "When should I plant beans in the Rift Valley?"
- "What is the price of maize in Nairobi today?"
- "How much DAP do I need for 2 acres of maize?"
- "Find me a certified seed dealer near Eldoret"

Or try in Kiswahili:  
"Mahindi yangu yana madoa ya kahawia. Ni ugonjwa gani?"
