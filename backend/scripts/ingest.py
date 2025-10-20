import os
import json
import uuid
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Config
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = "interview-questions"
MODEL_NAME = "all-MiniLM-L6-v2"
BASE_DIR = "F:/interview-SaaS/backend"
MODEL_PATH = os.path.join(BASE_DIR, "embedding", "models--sentence-transformers--all-MiniLM-L6-v2/snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf")  # local model folder
DATA_DIRECTORY = "F:/interview-SaaS/backend/scripts/final_output"

CLOUD = "aws"
REGION = "us-east-1"

# Init Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# ✅ Directly create new index
print(f"Creating index '{INDEX_NAME}'...")
pc.create_index(
    name=INDEX_NAME,
    dimension=384,  # MiniLM dimension
    metric="cosine",
    spec=ServerlessSpec(cloud=CLOUD, region=REGION)
)

index = pc.Index(INDEX_NAME)

# Load local model if available, else download once
if os.path.exists(MODEL_PATH):
    print(f"Loading model from local path: {MODEL_PATH}")
    model = SentenceTransformer(MODEL_PATH)
else:
    print("Downloading model for the first time...")
    model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_PATH)

# Collect JSON files
json_files = [f for f in os.listdir(DATA_DIRECTORY) if f.endswith(".json")]

batch_size = 100
upsert_data = []

for file_name in json_files:
    full_path = os.path.join(DATA_DIRECTORY, file_name)
    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    role_name = file_name.replace("_refined.json", "").replace("_", " ")

    for entry in tqdm(data, desc=f"Processing {file_name}"):
        q = entry.get("refined_question", "").strip()
        a = entry.get("answer", "").strip()

        # Skip invalid or garbage entries
        if not q or q.lower() == "not a valid question":
            continue  

        # Main searchable content
        page_content = f"Question: {q}\nAnswer: {a}"

        embedding = model.encode(page_content).tolist()

        # Metadata (extra context)
        metadata = {
            "role": entry.get("role", role_name),
            "skill": entry.get("skill", "N/A"),
            "difficulty": entry.get("difficulty", "N/A"),
            "source": entry.get("source", ""),
            "original_question": entry.get("original_question", ""),
            "answer": a
        }

        # ✅ Store page_content under "text" so retriever can build Document()
        upsert_data.append(
            (
                str(uuid.uuid4()),
                embedding,
                {"page_content": page_content, **metadata}
            )
        )

        # Batch upload
        if len(upsert_data) >= batch_size:
            index.upsert(vectors=upsert_data)
            upsert_data = []

# Final upload if leftover
if upsert_data:
    index.upsert(vectors=upsert_data)

print("✅ Data ingestion complete.")
print("Total vectors:", index.describe_index_stats())
