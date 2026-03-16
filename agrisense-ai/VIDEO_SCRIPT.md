# AgriSense AI — Demo Video Script
# Runtime: ~3 minutes
# Format: Screen recording + voiceover

## OPENING (0:00 – 0:20)
[Visuals: Aerial shot of African farmland → close-up of farmer's hands in soil → title card]

VOICEOVER:
"There are 500 million smallholder farmers in the world. 
They produce 70% of the food in developing countries.
And most of them have never spoken to an agronomist.
We built AgriSense AI to change that."

---

## ACT 1 — THE PROBLEM SOLVED (0:20 – 0:45)
[Visuals: Stats on screen → map of extension officer coverage]

VOICEOVER:
"One extension officer for every 2,500 farmers.
Crop losses of 25 to 40 percent per season — preventable losses.
AgriSense AI puts a full team of specialist AI agents 
in every farmer's pocket, in their language, on the phone they already have."

---

## ACT 2 — LIVE DEMO: WEB INTERFACE (0:45 – 1:30)
[Screen recording: Open the AgriSense AI web app]

VOICEOVER:
"Let's meet Mama Shamba — our AI farming companion, 
built on DigitalOcean Gradient AI."

[Type: "My maize leaves are turning yellow from the tips — what's wrong?"]

VOICEOVER:
"Mama Shamba routes this to our Crop Doctor agent, 
which searches our 2,000-entry disease knowledge base 
using Gradient AI's RAG pipeline..."

[Response appears with "Crop Doctor" badge]

VOICEOVER:
"...and diagnoses nitrogen deficiency versus leaf blight 
with confidence level and treatment steps.
All backed by a knowledge base stored in DigitalOcean Spaces 
and indexed with OpenSearch."

[Type: "How much fertiliser do I need for 2 acres of maize?"]

VOICEOVER:
"Now the Agronomy agent fires its fertiliser calculator function tool —
real calculations, exact bag quantities, organic alternatives included."

---

## ACT 3 — PHOTO DIAGNOSIS (1:30 – 1:55)
[Click "Diagnose Photo" → upload a crop disease photo]

VOICEOVER:
"Farmers can also send a photo of their sick crop.
We use GPT-4o vision via Gradient AI serverless inference
to analyse the image and cross-reference our disease database."

[Diagnosis appears]

VOICEOVER:
"A diagnosis with treatment plan — in seconds."

---

## ACT 4 — SMS DEMO (1:55 – 2:20)
[Switch to phone showing SMS conversation]

VOICEOVER:
"But not every farmer has a smartphone.
AgriSense AI works over basic SMS, reaching 35 African countries
via Africa's Talking.
The same Gradient AI agent, compressed to 160 characters."

[Show SMS: "HELP maize yellow tips" → response in under 160 chars]

VOICEOVER:
"No data plan. No smartphone. Same expert advice."

---

## ACT 5 — KISWAHILI (2:20 – 2:35)
[Back to web app]

VOICEOVER:
"And it speaks the farmer's language.
Watch Mama Shamba switch automatically to Kiswahili:"

[Type: "Mahindi yangu yana madoa ya kahawia. Ni ugonjwa gani?"]

[Response appears in Kiswahili]

VOICEOVER:
"Zero configuration. Gradient AI detects the language and responds in kind."

---

## CLOSING — ARCHITECTURE (2:35 – 3:00)
[Show architecture diagram: multi-agent routing diagram]

VOICEOVER:
"Under the hood, AgriSense AI uses the complete Gradient AI platform:
Multi-agent routing. Three knowledge bases with semantic RAG.
Function calling for live weather and market data.
Guardrails. Agent evaluations. Full tracing.
All deployed on DigitalOcean App Platform — from one YAML file.

AgriSense AI. Every farmer deserves an agronomist."

[End card: GitHub URL, Demo URL, "Built with DigitalOcean Gradient AI"]

---

## RECORDING TIPS
- Use OBS Studio at 1920x1080, 30fps
- Record the full browser window (no cursor effects)
- Add simple transitions between sections (cut, no fancy effects)
- Voiceover: record separately in Audacity or GarageBand, normalize to -16 LUFS
- Background music: royalty-free African acoustic guitar at -20dB under voice
- Upload as Unlisted on YouTube initially, set to Public before submitting

## KEY TALKING POINTS FOR Q&A
1. "Why Gradient AI specifically?" — native multi-agent routing, RAG with DO Spaces integration, one platform for the whole stack
2. "What's the business model?" — freemium (free for subsistence farmers, paid API for NGOs and agtech companies)
3. "How do you handle accuracy?" — automated evaluation pipeline blocks deploys below 85% correctness, human agronomist review quarterly
4. "Scale?" — DO App Platform autoscales, Gradient AI handles serverless inference
