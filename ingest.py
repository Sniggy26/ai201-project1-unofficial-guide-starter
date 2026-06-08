import os
import glob
import random

def load_docs(folder="docs"):
    """Load all .txt files from the docs folder."""
    files = glob.glob(f"{folder}/*.txt")
    docs = []
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            text = file.read()
        docs.append({
            "source": os.path.basename(f),
            "text": text
        })
    print(f"Loaded {len(docs)} documents")
    return docs

def clean(text):
    """Clean document text — remove extra whitespace and blank lines."""
    # Remove extra whitespace
    lines = text.splitlines()
    # Remove lines that are just whitespace or very short (nav artifacts)
    cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 2]
    # Join back and collapse multiple blank lines
    cleaned = "\n".join(cleaned_lines)
    return cleaned.strip()

def chunk(text, source, size=400, overlap=50):
    """Split text into chunks of ~size characters with overlap."""
    chunks = []
    start = 0
    chunk_index = 0
    while start < len(text):
        end = start + size
        chunk_text = text[start:end].strip()
        if len(chunk_text) > 20:  # skip tiny leftover chunks
            chunks.append({
                "text": chunk_text,
                "source": source,
                "chunk_id": f"{source}_chunk_{chunk_index}"
            })
            chunk_index += 1
        start += size - overlap
    return chunks

def run_pipeline(folder="docs"):
    """Run the full ingestion pipeline and return all chunks."""
    docs = load_docs(folder)
    all_chunks = []

    for doc in docs:
        cleaned_text = clean(doc["text"])
        doc_chunks = chunk(cleaned_text, doc["source"])
        all_chunks.extend(doc_chunks)
        print(f"  {doc['source']}: {len(doc_chunks)} chunks")

    print(f"\nTotal chunks: {len(all_chunks)}")
    return all_chunks

if __name__ == "__main__":
    all_chunks = run_pipeline()

    # Print 5 random chunks so you can inspect them
    print("\n" + "="*60)
    print("SAMPLE CHUNKS (5 random):")
    print("="*60)
    sample = random.sample(all_chunks, min(5, len(all_chunks)))
    for i, chunk in enumerate(sample, 1):
        print(f"\n--- Chunk {i} | Source: {chunk['source']} ---")
        print(chunk["text"])
        print()
