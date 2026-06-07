# Project Planning: GSU Unofficial Campus Survival Guide

## Domain

Georgia State University students rely heavily on unofficial, peer-shared knowledge to survive college — which holds to clear, which professors are actually helpful, how MARTA works, how to not get dropped from your classes. This knowledge lives scattered across Reddit threads, Discord servers, and word of mouth. Official GSU websites exist but are dense, hard to navigate, and don't answer the real questions students have. This RAG system makes that practical, student-centered knowledge searchable and answerable through plain-language questions.

---

## Documents

10 source documents covering different survival topics for GSU students:

| File | Topic | Source |
|---|---|---|
| `docs/marta_upass.txt` | MARTA UPass program, Breeze cards, transit tips | parking.gsu.edu + student knowledge |
| `docs/paws_guide.txt` | PAWS portal — registration, holds, DegreeWorks | paws.gsu.edu + student knowledge |
| `docs/financial_aid.txt` | Financial aid, FAFSA, accepting awards, HOPE scholarship | sfs.gsu.edu + student knowledge |
| `docs/advisement.txt` | Academic advising, drop/add, registration tips | advisement.gsu.edu + student knowledge |
| `docs/find_help.txt` | Who to contact for every kind of problem at GSU | engagement.gsu.edu + student knowledge |
| `docs/icollege_guide.txt` | iCollege (D2L) tips, online classes, notifications | icollege.gsu.edu + student knowledge |
| `docs/housing_faq.txt` | On-campus housing, off-campus tips, roommates | myhousing.gsu.edu + student knowledge |
| `docs/dining.txt` | PantherDining locations, meal plans, food budget tips | dining.gsu.edu + student knowledge |
| `docs/student_reviews.txt` | Real student reviews of campus life, academic experience | Student reviews + community knowledge |
| `docs/safety_downtown.txt` | Downtown Atlanta safety, LiveSafe app, MARTA safety | safety.gsu.edu + student knowledge |

---

## Chunking Strategy

**Chunk size:** 400 characters
**Overlap:** 50 characters

**Why these numbers fit my documents:**

My documents are a mix of structured guides and short student-advice paragraphs. Key facts tend to appear in 2–4 sentence bursts — for example, "how to get a MARTA pass" is explained in about 3 sentences. A 400-character chunk is large enough to capture one complete idea (a tip, a step, a policy explanation) without merging multiple unrelated topics into one chunk.

The 50-character overlap ensures that if a key fact spans a chunk boundary — for example, a step that starts at the end of one chunk and finishes at the start of the next — at least one of the chunks will contain enough context to be retrievable.

Chunks that are too small (under 150 characters) would produce fragments like "Check your PAWS account" with no context about what to check or why, making them impossible to match to specific queries. Chunks that are too large (over 800 characters) would dilute the embedding — a chunk covering MARTA, PAWS, and housing all at once would match weakly to any specific query about one of those topics.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

This model runs entirely locally — no API key, no rate limits, no cost. It produces 384-dimension embeddings and is well-suited for short to medium-length English text, which matches my document type.

**Top-k:** 5 chunks per query

Retrieving 5 chunks gives the LLM enough context to synthesize a complete answer (e.g., combining a "how to" step with a student tip from a different document) without flooding it with loosely related material that could pull the response off-topic.

**Production tradeoffs I would consider:**
- `text-embedding-3-small` (OpenAI): Higher accuracy on domain-specific queries, supports longer context windows, but costs money per API call and requires internet access
- `multilingual-e5-large`: Better for multilingual student populations, but heavier and slower
- `all-mpnet-base-v2`: Slightly more accurate than MiniLM but 3x slower — fine for a small corpus like this, but would not scale well to millions of documents
- For a real production system, I'd use an API-based embedding model for accuracy, with a local fallback for cost control

**Why semantic search works here:**
A student asking "how do I get a cheaper train pass" will retrieve the MARTA UPass chunk even though it never uses the word "cheaper" or "train pass" — because the embedding model understands meaning, not just exact words.

---

## Evaluation Plan

| # | Test Question | Expected Correct Answer |
|---|---|---|
| 1 | How do I get a discounted MARTA pass as a GSU student? | Log into the GSU Parking Portal, purchase a discounted monthly calendar pass for $61, wait for a confirmation email, then pick up your Breeze Card at the UBS Center |
| 2 | What should I do if I have a hold on my PAWS account? | Check PAWS to see the contact listed on the hold, then email registrar@gsu.edu — holds must be cleared before registration or you cannot enroll in classes |
| 3 | How do I accept my financial aid award at GSU? | Log into PAWS, go to the Finances tab, manually accept federal loans and work-study (Pell Grant is auto-accepted), and do not accept aid for semesters you won't be enrolled |
| 4 | Where do I go for academic advising if I'm a new student? | Attend New Student Orientation where you meet with advisors; use the advisor search tool at advisement.gsu.edu to find your assigned advisor by college |
| 5 | What safety resources does GSU offer for students in downtown Atlanta? | Download the LiveSafe app for safety escorts and emergency contacts, sign up for emergency alerts at getrave.com/login/gsu, and call GSU Police non-emergency at 404-413-3333 |

---

## Anticipated Challenges

**1. Key facts split across chunk boundaries**
Some how-to steps span multiple sentences that could end up in different chunks. For example, the 5-step process for getting a MARTA pass might be split so that steps 1–3 are in one chunk and steps 4–5 are in another. The 50-character overlap reduces this risk but does not eliminate it. If retrieval returns only half a process, the LLM's answer will be incomplete.

**2. Multiple documents covering overlapping topics**
Several documents touch related topics — for example, `find_help.txt` mentions financial aid, and `financial_aid.txt` covers the same topic in more depth. This could cause retrieval to return chunks from both files for a financial aid question. The LLM should handle this fine, but it could also cause confusion if the chunks give slightly different advice.

**3. Out-of-scope questions producing hallucinated answers**
If a student asks something not covered in any document (e.g., "What's the best bar near GSU?"), the grounding instruction must be strong enough to make the LLM say it doesn't know rather than pulling from its general training knowledge.

---

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌───────────────────────────┐
│  Raw Documents  │────▶│   ingest.py  │────▶│        ChromaDB           │
│  (docs/*.txt)   │     │  - load      │     │  - all-MiniLM-L6-v2       │
│  10 .txt files  │     │  - clean     │     │    embeddings             │
│  pdfplumber     │     │  - chunk     │     │  - source metadata        │
│  for any PDFs   │     │  400c / 50c  │     │  - persistent storage     │
└─────────────────┘     └──────────────┘     └───────────────┬───────────┘
                                                              │
                                                    top-5 semantic search
                                                              │
┌─────────────────┐     ┌──────────────┐     ┌───────────────▼───────────┐
│   Gradio UI     │◀────│   query.py   │◀────│       retrieve()          │
│   app.py        │     │  - prompt    │     │  - query embedding        │
│  - text input   │     │    template  │     │  - cosine similarity      │
│  - answer out   │     │  - grounding │     │  - returns chunks +       │
│  - sources out  │     │  - Groq LLM  │     │    source metadata        │
└─────────────────┘     │  llama-3.3   │     └───────────────────────────┘
                        │  -70b        │
                        └──────────────┘
```

**Tools at each stage:**
- Document Ingestion: Python `open()` / `pdfplumber`
- Chunking: Custom Python function (character-based, 400c chunks, 50c overlap)
- Embedding + Vector Store: `sentence-transformers` (all-MiniLM-L6-v2) + `ChromaDB`
- Retrieval: ChromaDB semantic similarity search, top-k=5
- Generation: Groq API (`llama-3.3-70b-versatile`)
- Interface: Gradio (`gr.Blocks`)

---

## AI Tool Plan

| Pipeline Component | What I'll give the AI | What I expect it to produce |
|---|---|---|
| `ingest.py` (loading + chunking) | This Documents section, the Chunking Strategy section, and the Architecture diagram | A script that loads all .txt files from docs/, cleans them (strip extra whitespace and non-content lines), and produces chunks of ~400 characters with 50-character overlap, printing 5 sample chunks |
| `embed.py` (embedding + ChromaDB) | The Retrieval Approach section and Architecture diagram | A script that loads chunks from ingest.py, embeds them with all-MiniLM-L6-v2, stores them in a ChromaDB PersistentClient at ./chroma_db with source metadata, and prints total chunk count |
| `query.py` (retrieval + generation) | The Retrieval Approach section, grounding requirement, and the 5 evaluation questions | A function ask(question) that retrieves top-5 chunks, builds a grounded prompt, calls Groq llama-3.3-70b-versatile, and returns a dict with answer and sources list |
| `app.py` (Gradio interface) | The Architecture diagram and the ask() function signature | A Gradio Blocks app with a question textbox, Ask button, answer output, and sources output |

I will review all generated code to confirm it matches my spec, ask the AI to explain anything I don't understand, and manually fix anything that doesn't match the chunking strategy or grounding requirements above.
