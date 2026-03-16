"""
AgriSense AI — Knowledge Base Setup Script
==========================================
Creates and indexes all Gradient AI knowledge bases on DigitalOcean Spaces.
Run once before deploying agents.

Usage: python scripts/setup_knowledge_bases.py
"""

import os
import json
import boto3
from gradientai import GradientAI

client = GradientAI(api_key=os.environ["DIGITALOCEAN_API_TOKEN"])

DO_SPACES_KEY = os.environ["DO_SPACES_KEY"]
DO_SPACES_SECRET = os.environ["DO_SPACES_SECRET"]
DO_SPACES_REGION = os.environ.get("DO_SPACES_REGION", "nyc3")
DO_SPACES_BUCKET = "agrisense-knowledge-base"


def get_spaces_client():
    """Create S3-compatible client for DigitalOcean Spaces."""
    return boto3.client(
        "s3",
        region_name=DO_SPACES_REGION,
        endpoint_url=f"https://{DO_SPACES_REGION}.digitaloceanspaces.com",
        aws_access_key_id=DO_SPACES_KEY,
        aws_secret_access_key=DO_SPACES_SECRET,
    )


def upload_knowledge_documents():
    """Upload all knowledge documents to DigitalOcean Spaces."""
    spaces = get_spaces_client()
    
    # Create bucket if not exists
    try:
        spaces.create_bucket(Bucket=DO_SPACES_BUCKET)
        print(f"✓ Created bucket: {DO_SPACES_BUCKET}")
    except Exception:
        print(f"  Bucket already exists: {DO_SPACES_BUCKET}")
    
    # Upload crop diseases database
    print("\n📚 Uploading crop diseases knowledge base...")
    upload_directory(spaces, "knowledge/crop_diseases/", "crop-diseases/")
    
    # Upload agronomy guides
    print("\n🌱 Uploading agronomy guides knowledge base...")
    upload_directory(spaces, "knowledge/agronomy_guides/", "agronomy-guides/")
    
    # Upload supplier directory
    print("\n🏪 Uploading supplier directory knowledge base...")
    upload_directory(spaces, "knowledge/supplier_directory/", "supplier-directory/")
    
    print("\n✅ All documents uploaded to DigitalOcean Spaces!")


def upload_directory(spaces_client, local_dir: str, prefix: str):
    """Upload all files in a local directory to Spaces."""
    if not os.path.exists(local_dir):
        print(f"  Warning: {local_dir} not found, creating sample data...")
        create_sample_knowledge_data(local_dir)
    
    count = 0
    for filename in os.listdir(local_dir):
        if filename.startswith("."):
            continue
        local_path = os.path.join(local_dir, filename)
        spaces_key = f"{prefix}{filename}"
        
        with open(local_path, "rb") as f:
            spaces_client.put_object(
                Bucket=DO_SPACES_BUCKET,
                Key=spaces_key,
                Body=f.read(),
                ACL="private",
            )
        count += 1
        print(f"  ✓ Uploaded: {spaces_key}")
    
    print(f"  Total: {count} files uploaded")


def create_gradient_knowledge_bases():
    """Create and configure Gradient AI knowledge bases."""
    
    kbs = [
        {
            "name": "agrisense-crop-diseases",
            "description": "Comprehensive database of crop diseases, pests, and nutrient deficiencies for African smallholder crops",
            "spaces_prefix": "crop-diseases/",
            "chunking_strategy": "semantic",
            "embedding_model": "text-embedding-3-large",
        },
        {
            "name": "agrisense-agronomy-guides",
            "description": "Regional agronomy guides covering soil management, fertiliser recommendations, and planting calendars",
            "spaces_prefix": "agronomy-guides/",
            "chunking_strategy": "section_based",
            "embedding_model": "text-embedding-3-large",
        },
        {
            "name": "agrisense-supplier-directory",
            "description": "Directory of verified agro-dealers and input suppliers across East and West Africa",
            "spaces_prefix": "supplier-directory/",
            "chunking_strategy": "fixed_length",
            "embedding_model": "text-embedding-3-small",   # Faster for structured data
        },
    ]
    
    created_kb_ids = {}
    
    for kb_config in kbs:
        print(f"\n🔧 Creating knowledge base: {kb_config['name']}")
        
        kb = client.knowledge_bases.create(
            name=kb_config["name"],
            description=kb_config["description"],
            embedding_model=kb_config["embedding_model"],
        )
        
        kb_id = kb.id
        print(f"  ✓ Created KB: {kb_id}")
        
        # Add DigitalOcean Spaces as data source
        client.knowledge_bases.add_data_source(
            knowledge_base_id=kb_id,
            data_source={
                "type": "spaces",
                "bucket": DO_SPACES_BUCKET,
                "prefix": kb_config["spaces_prefix"],
                "region": DO_SPACES_REGION,
            },
            chunking_strategy={
                "type": kb_config["chunking_strategy"],
                "chunk_size": 512,
                "chunk_overlap": 50,
            },
        )
        
        # Start indexing
        index_job = client.knowledge_bases.start_indexing(knowledge_base_id=kb_id)
        print(f"  🔄 Indexing started: {index_job.id}")
        
        created_kb_ids[kb_config["name"]] = kb_id
    
    # Print environment variables to set
    print("\n\n✅ Knowledge bases created! Add these to your .env:\n")
    print(f"CROP_DISEASES_KB_ID={created_kb_ids.get('agrisense-crop-diseases', '')}")
    print(f"AGRONOMY_KB_ID={created_kb_ids.get('agrisense-agronomy-guides', '')}")
    print(f"SUPPLIER_KB_ID={created_kb_ids.get('agrisense-supplier-directory', '')}")
    
    return created_kb_ids


def create_sample_knowledge_data(directory: str):
    """Create sample knowledge data files for demonstration."""
    os.makedirs(directory, exist_ok=True)
    
    if "crop_diseases" in directory:
        diseases = [
            {
                "name": "Maize Lethal Necrosis (MLN)",
                "crops_affected": ["maize", "corn"],
                "symptoms": "Yellowing from leaf tips inward, brown streaking, premature plant death, ear rotting",
                "cause": "Co-infection of Maize Chlorotic Mottle Virus (MCMV) and Sugarcane Mosaic Virus (SCMV)",
                "spread": "Thrips, aphids, beetles; infected seed",
                "treatment": "No cure. Remove and destroy infected plants immediately. Do not compost.",
                "prevention": "Plant MLN-tolerant varieties (e.g. SEEDCO SC403), control insect vectors with appropriate pesticides",
                "severity": "CRITICAL",
                "regions": ["Kenya", "Tanzania", "Ethiopia", "Uganda"],
                "report_to": "Local agriculture extension officer immediately — notifiable disease",
            },
            {
                "name": "Bean Rust",
                "crops_affected": ["beans", "french beans", "climbing beans"],
                "symptoms": "Small, circular, rust-colored pustules on undersides of leaves; yellow halos on upper leaf surface; leaves may drop",
                "cause": "Uromyces appendiculatus fungus",
                "spread": "Wind, rain splash, infected plant debris",
                "treatment": "Apply mancozeb or copper-based fungicide at first signs. Repeat every 10-14 days.",
                "prevention": "Plant resistant varieties, ensure good air circulation, avoid overhead irrigation",
                "severity": "MODERATE",
                "regions": ["All bean-growing regions"],
            },
            {
                "name": "Fall Armyworm",
                "crops_affected": ["maize", "sorghum", "wheat", "millet"],
                "symptoms": "Ragged feeding damage on leaves, 'windowpane' feeding in young plants, frass (excrement) in plant whorl, characteristic C-shaped markings on caterpillar",
                "cause": "Spodoptera frugiperda moth larvae",
                "spread": "Wind-borne adult moths can travel hundreds of kilometers",
                "treatment": "Emamectin benzoate, spinosad, or chlorpyrifos. Spray into leaf whorl. Biopesticides: Bacillus thuringiensis (Bt) for early instar larvae.",
                "prevention": "Early planting, push-pull intercropping with Desmodium and Napier grass, egg mass scouting",
                "severity": "CRITICAL",
                "regions": ["Pan-African"],
                "report_to": "Extension officer — widespread invasive pest",
            },
        ]
        
        for disease in diseases:
            filename = disease["name"].lower().replace(" ", "_").replace("(", "").replace(")", "") + ".json"
            with open(os.path.join(directory, filename), "w") as f:
                json.dump(disease, f, indent=2)
        
        print(f"  ✓ Created {len(diseases)} sample disease entries in {directory}")
    
    elif "agronomy_guides" in directory:
        guide = """# East Africa Maize Planting Guide

## Overview
Maize (Zea mays) is the most important food crop in East Africa, grown by over 30 million 
smallholder farming households.

## Soil Requirements
- pH: 5.5 – 7.0 (test with local extension service)
- Well-drained loam or clay-loam soils
- Avoid waterlogged areas

## Planting Calendar — Kenya
| Region | Long Rains (Season A) | Short Rains (Season B) |
|--------|----------------------|------------------------|
| Central Highlands | March – April | October – November |
| Rift Valley | February – March | October |
| Western Kenya | February – March | August – September |
| Coast | April – May | November |

## Seed Selection
- **Drought-tolerant varieties**: WEMA drought-tolerant, DT maize varieties from CIMMYT
- **High-yield hybrids**: H614D, H6213, DK8031
- **Spacing**: 75cm between rows × 25cm between plants (53,000 plants/ha)

## Fertiliser Programme
### Planting fertiliser (apply at planting)
- 50 kg/ha DAP (Di-Ammonium Phosphate)
- Alternative: 3–4 tablespoons of CAN per planting hole

### Top dressing (4–6 weeks after planting)
- 50 kg/ha CAN (Calcium Ammonium Nitrate)
- Apply when soil is moist, NOT in dry conditions

### Organic options
- 5 tonnes/ha of well-composted manure incorporated before planting
- Combine with 25 kg/ha DAP for best results
"""
        with open(os.path.join(directory, "maize_east_africa_guide.md"), "w") as f:
            f.write(guide)
        print(f"  ✓ Created sample agronomy guide in {directory}")


if __name__ == "__main__":
    print("🌱 AgriSense AI — Knowledge Base Setup")
    print("=" * 50)
    
    print("\n1. Uploading documents to DigitalOcean Spaces...")
    upload_knowledge_documents()
    
    print("\n2. Creating Gradient AI knowledge bases...")
    create_gradient_knowledge_bases()
    
    print("\n✅ Setup complete! Your knowledge bases are indexing.")
    print("   Indexing typically takes 5-15 minutes.")
    print("   Check status in the DigitalOcean console → Gradient AI → Knowledge Bases")
