import json
import hashlib
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

from app.config import settings  # your config module

# Configuration
PINECONE_INDEX_NAME = "interview-knowledge-base"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def hash_id(text: str) -> str:
    """
    Creates a short unique hash for IDs (to avoid overly long IDs from URLs).
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]


def prepare_documents_for_pinecone(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes the raw scraped data into a flat list of documents
    ready for embedding and upserting.
    """
    documents = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    for role_data in data:
        role = role_data.get("role")
        for source in role_data.get("sources", []):
            url = source.get("url", "unknown")
            for qa_pair in source.get("qa_pairs", []):
                question = qa_pair.get("question", "").strip()
                answer = qa_pair.get("answer", "").strip()
                if not question or not answer:
                    continue  # skip incomplete pairs

                combined_text = f"Question: {question}\nAnswer: {answer}"
                chunks = text_splitter.split_text(combined_text)

                for i, chunk in enumerate(chunks):
                    unique_id = f"{role}-{hash_id(url)}-{i}"
                    documents.append({
                        "id": unique_id,
                        "text": chunk,
                        "metadata": {
                            "role": role,
                            "question": question,
                            "source": url,
                            "type": "interview_qa",  # default type
                            "experience_level": "general"  # can refine later
                        }
                    })
    return documents


def main():
    """
    Orchestrates data ingestion into Pinecone.
    """
    print("🚀 Starting data ingestion process...")

    # 1. Load Scraped Data
    try:
        with open("scraped_data.json", "r", encoding="utf-8") as f:
            scraped_data = json.load(f)
        print(f"✅ Loaded {len(scraped_data)} roles from scraped_data.json")
    except FileNotFoundError:
        print("❌ Error: scraped_data.json not found. Please run scraper.py first.")
        return

    # 2. Prepare Documents
    documents = prepare_documents_for_pinecone(scraped_data)
    print(f"📄 Prepared {len(documents)} document chunks for ingestion.")

    if not documents:
        print("⚠️ No documents to ingest. Exiting.")
        return

    # 3. Initialize Embeddings
    print(f"🔍 Initializing embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # 4. Initialize Pinecone
    print("🔗 Connecting to Pinecone...")
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)

    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"🆕 Creating Pinecone index: {PINECONE_INDEX_NAME}")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384,  # all-MiniLM-L6-v2 has 384 dimensions
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    index = pc.Index(PINECONE_INDEX_NAME)
    print("✅ Pinecone index ready.")

    # 5. Embed + Upsert in batches
    batch_size = 100
    print(f"⬆️ Ingesting in batches of {batch_size}...")
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        texts = [doc["text"] for doc in batch]

        # Embed
        vectors = embeddings.embed_documents(texts)

        # Prepare vectors
        upserts = [
            {"id": doc["id"], "values": vectors[j], "metadata": doc["metadata"]}
            for j, doc in enumerate(batch)
        ]

        # Upsert
        index.upsert(vectors=upserts)
        print(f"  -> Upserted batch {i // batch_size + 1}/{(len(documents) + batch_size - 1) // batch_size}")

    print("\n✅ Data ingestion complete!")
    print(f"📊 Total vectors in index: {index.describe_index_stats()['total_vector_count']}")


if __name__ == "__main__":
    main()
