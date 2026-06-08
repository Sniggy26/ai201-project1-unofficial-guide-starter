import os
from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

# Load model and ChromaDB collection once at startup
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("gsu_docs")

# Set up Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def retrieve(query, k=5):
    """Retrieve top-k relevant chunks for a query."""
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    return chunks, metadatas


def ask(question):
    """Retrieve relevant chunks and generate a grounded answer."""
    chunks, metadatas = retrieve(question)

    # Build context from retrieved chunks
    context = "\n\n".join(
        f"[Source: {meta['source']}]\n{chunk}"
        for chunk, meta in zip(chunks, metadatas)
    )

    # Get unique source files used
    sources = list(set(meta["source"] for meta in metadatas))

    # Grounded prompt — model must answer only from context
    prompt = f"""You are a helpful assistant for Georgia State University students.
Answer the student's question using ONLY the information provided in the documents below.
If the documents do not contain enough information to answer the question, say exactly:
"I don't have enough information on that in my GSU guide."
Do not use any outside knowledge. Always cite which document your answer comes from.

Documents:
{context}

Student Question: {question}

Answer:"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1000
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": sources
    }


if __name__ == "__main__":
    # Quick end-to-end test
    print("\n" + "="*60)
    print("END-TO-END TEST")
    print("="*60)

    test_questions = [
        "How do I get a discounted MARTA pass as a GSU student?",
        "What should I do if I have a hold on my PAWS account?",
        "What is the best pizza place in Atlanta?"  # out-of-scope test
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        print("-" * 50)
        result = ask(q)
        print(f"A: {result['answer']}")
        print(f"\nSources: {', '.join(result['sources'])}")
        print()
