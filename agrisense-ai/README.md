# 🌱 AgriSense AI — Precision Agriculture for Smallholder Farmers

> **DigitalOcean Gradient™ AI Hackathon Submission**
> Built by leveraging the full Gradient AI Platform stack: multi-agent routing, RAG knowledge bases, guardrails, serverless inference, function calling, agent evaluations, and full observability.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: DigitalOcean Gradient AI](https://img.shields.io/badge/Platform-Gradient%20AI-0080FF)](https://www.digitalocean.com/products/gradient)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)

---

## 🏆 Prize Categories Targeted

| Category | Why AgriSense qualifies |
|---|---|
| **1st Place** | Full Gradient AI feature coverage, production-ready architecture |
| **Best Program for the People** | Serves 500M+ smallholder farmers with limited tech access |
| **Best AI Agent Persona** | "Mama Shamba" — a warm, multilingual farming companion persona |
| **The Great Whale Prize** | Promotes sustainable, climate-resilient agriculture practices |

---

## 🌍 What Is AgriSense AI?

AgriSense AI is a **multi-agent precision agriculture platform** that gives smallholder farmers in Africa and the developing world access to expert agronomic advice, crop disease diagnosis, real-time weather insights, and live market prices — in their local language, via the channel they already use (SMS, WhatsApp, or web).

### The Problem
- 500M+ smallholder farmers worldwide manage ~70% of food production in developing countries
- Average farm size: 1–2 hectares
- Access to agronomists: 1 per 1,000+ farmers in Sub-Saharan Africa
- Result: preventable crop losses of **25–40%** per season due to disease, poor timing, and mispriced sales

### The Solution
AgriSense AI acts as a **24/7 AI agronomist** accessible via:
- 📱 SMS / USSD (no smartphone needed)
- 💬 WhatsApp
- 🌐 Web app
- 🔌 REST API (for NGO/government integrations)

---

## 🏗️ Architecture Overview

```
User (SMS/WhatsApp/Web)
        ↓
  [API Gateway — FastAPI on DO App Platform]
        ↓
  [Orchestrator Agent "Mama Shamba" — Gradient AI Multi-Agent Router]
        ↓ routes to ↓
┌─────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  Crop Doctor │ Weather Agent│ Market Agent │Agronomy Agent│ Input Finder │
│  (RAG +      │ (function    │ (function    │ (RAG +       │ (RAG +       │
│   vision)    │  calling)    │  calling)    │  knowledge)  │  geo-search) │
└─────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
        ↓
  [Gradient AI Platform]
  • Serverless Inference (GPT-4o, Claude Sonnet 4.6, Llama 3.1)
  • Knowledge Bases (DO Spaces + OpenSearch) 
  • RAG with semantic chunking
  • Guardrails (content moderation + jailbreak)
  • Agent Evaluations + Tracing
        ↓
  [DigitalOcean Infrastructure]
  • DO App Platform (backend + frontend)
  • DO Spaces (knowledge base documents)
  • GPU Droplet (vision model for crop disease images)
```

---

## 🤖 Gradient AI Features Used

### 1. Multi-Agent Routing
The **Orchestrator Agent "Mama Shamba"** uses Gradient AI's built-in agent routing to classify each farmer query and dispatch to the correct specialist agent. No custom routing logic needed.

### 2. Knowledge Bases (RAG)
Three knowledge bases powered by DO Spaces + OpenSearch:
- `crop-diseases-kb` — 2,000+ disease entries with symptoms, treatments, photos
- `agronomy-kb` — Regional planting guides, soil management, fertiliser recommendations  
- `input-suppliers-kb` — Verified agro-dealer directory by GPS region

Chunking strategy: **semantic** for disease descriptions, **section-based** for guides.

### 3. Serverless Inference
- Primary: **Claude Sonnet 4.6** (reasoning + long context for complex queries)
- Fast responses: **Llama 3.1 70B** (SMS-length replies)
- Vision: **GPT-4o** (crop disease photo analysis)

### 4. Guardrails
- **Content Moderation** — prevents off-topic or harmful outputs
- **Jailbreak protection** — keeps agents focused on agriculture
- **Sensitive Data** — strips any PII from logs

### 5. Function Calling
Agents call live external functions:
- `get_weather_forecast(lat, lng, days)` → OpenWeatherMap API
- `get_market_prices(crop, region)` → local commodity exchange APIs
- `get_nearby_dealers(lat, lng, product)` → geo-indexed supplier lookup

### 6. Agent Evaluations
Automated test suite with 150+ agricultural Q&A pairs:
```bash
gradient agent evaluate \
  --test-case-name "crop-disease-accuracy" \
  --dataset-file evals/crop_disease_dataset.csv \
  --categories correctness,context_quality,safety_and_security \
  --success-threshold 85.0
```

### 7. Tracing + Observability
Full trace capture on every agent call for debugging, continuous improvement, and audit trails for NGO partners.

### 8. Agent Development Kit (ADK)
Built with the **Gradient ADK** for local dev → production deployment pipeline:
```bash
gradient agent run --dev   # local hot-reload
gradient agent deploy      # push to DO production
gradient agent logs        # stream live logs
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- DigitalOcean account with Gradient AI enabled
- DigitalOcean API token

### 1. Clone & install
```bash
git clone https://github.com/yourusername/agrisense-ai
cd agrisense-ai
pip install -r backend/requirements.txt
cd frontend && npm install
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in:
# DIGITALOCEAN_API_TOKEN=your_token
# GRADIENT_AGENT_ENDPOINT=your_endpoint
# GRADIENT_AGENT_KEY=your_key
# OPENWEATHER_API_KEY=your_key
# AFRICASTALKING_API_KEY=your_key (for SMS)
```

### 3. Set up knowledge bases
```bash
python scripts/setup_knowledge_bases.py
# Uploads disease DB, agronomy guides, supplier directory to DO Spaces
# Creates and indexes Gradient AI knowledge bases
```

### 4. Deploy agents
```bash
cd backend
gradient agent deploy
```

### 5. Run frontend
```bash
cd frontend
npm run dev
```

---

## 📁 Project Structure

```
agrisense-ai/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py       # Mama Shamba — main routing agent
│   │   ├── crop_doctor.py        # Disease diagnosis agent
│   │   ├── weather_agent.py      # Weather + planting calendar agent
│   │   ├── market_agent.py       # Commodity price intelligence
│   │   ├── agronomy_agent.py     # Soil, fertiliser, seed advice
│   │   └── input_finder.py       # Nearby supplier search
│   ├── functions/
│   │   ├── weather.py            # OpenWeatherMap function
│   │   ├── market_prices.py      # Commodity API function
│   │   └── geo_search.py         # Geospatial dealer lookup
│   ├── api/
│   │   ├── main.py               # FastAPI application
│   │   ├── sms_webhook.py        # Africa's Talking SMS handler
│   │   └── whatsapp_webhook.py   # WhatsApp webhook handler
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/           # React UI components
│   │   ├── pages/                # App pages
│   │   └── hooks/                # Custom React hooks
│   └── package.json
├── knowledge/
│   ├── crop_diseases/            # Disease JSON database
│   ├── agronomy_guides/          # Regional farming guides (PDF/MD)
│   └── supplier_directory/       # Agro-dealer database (CSV)
├── evals/
│   ├── crop_disease_dataset.csv  # Evaluation test cases
│   ├── market_query_dataset.csv
│   └── agronomy_dataset.csv
├── scripts/
│   ├── setup_knowledge_bases.py  # KB creation + indexing
│   └── seed_test_data.py
├── .env.example
├── gradient.yaml                 # Agent config for ADK
└── README.md
```

---

## 📊 Impact Metrics

| Metric | Value |
|---|---|
| Target farmers | 500M+ smallholders globally |
| Languages supported | English, Kiswahili, French, Hausa |
| Avg. response time | < 3s (web), < 8s (SMS) |
| Crops covered | 120+ |
| Diseases in knowledge base | 2,000+ |
| Countries initially targeted | Kenya, Uganda, Tanzania, Nigeria, Ghana |

---

## 🔒 Data Privacy
- Open-source models (Llama 3.1) used for all personally sensitive queries
- Data stays within DigitalOcean's infrastructure
- Guardrails strip PII before logging
- No farmer data sold or shared

---

## 📄 License
MIT — see [LICENSE](LICENSE)
