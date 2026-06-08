import chromadb
from sentence_transformers import SentenceTransformer
from ingest import run_pipeline

def build_vector_store(folder="docs"):
    """Embed all chunks and store them in ChromaDB."""

    # Load and chunk all documents
    print("Running ingestion pipeline...")
    all_chunks = run_pipeline(folder)

    # Load the embedding model (runs locally, no API key needed)
    print("\nLoading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Set up ChromaDB — saves to disk so you don't re-embed every time
    print("Setting up ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")

    # Delete existing collection if it exists (clean rebuild)
    try:
        client.delete_collection("gsu_docs")
        print("Cleared existing collection")
    except:
        pass

    collection = client.create_collection("gsu_docs")

    # Embed and store all chunks
    print(f"\nEmbedding {len(all_chunks)} chunks... (this may take 30-60 seconds)")
    texts = [c["text"] for c in all_chunks]
    ids = [c["chunk_id"] for c in all_chunks]
    metadatas = [{"source": c["source"]} for c in all_chunks]

    embeddings = model.encode(texts, show_progress_bar=True)

    collection.add(
        documents=texts,
        embeddings=embeddings.tolist(),
        ids=ids,
        metadatas=metadatas
    )

    print(f"\nDone! {collection.count()} chunks stored in ChromaDB.")
    return collection, model


def retrieve(query, collection, model, k=5):
    """Retrieve top-k most relevant chunks for a query."""
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    return chunks, metadatas, distances


if __name__ == "__main__":
    # Build the vector store
    collection, model = build_vector_store()

    # Test retrieval with 3 of your evaluation questions
    test_queries = [
        "How do I get a discounted MARTA pass as a GSU student?",
        "What should I do if I have a hold on my PAWS account?",
        "What safety resources does GSU offer for students in downtown Atlanta?"
    ]

    print("\n" + "="*60)
    print("RETRIEVAL TEST (3 evaluation questions)")
    print("="*60)

    for query in test_queries:
        print(f"\nQUERY: {query}")
        print("-" * 50)
        chunks, metadatas, distances = retrieve(query, collection, model)
        for i, (chunk, meta, dist) in enumerate(zip(chunks, metadatas, distances), 1):
            print(f"\n  Result {i} | Source: {meta['source']} | Distance: {dist:.3f}")
            print(f"  {chunk[:200]}...")
        print()
