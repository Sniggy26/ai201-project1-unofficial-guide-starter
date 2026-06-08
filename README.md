# GSU Unofficial Campus Survival Guide — RAG System

A Retrieval-Augmented Generation (RAG) system that makes Georgia State University student knowledge searchable and answerable. Students ask plain-language questions — "How do I get a discounted MARTA pass?" or "What do I do if I have a hold on PAWS?" — and get grounded, cited answers drawn from real GSU documents.

---

## Domain and Document Sources

**Domain:** Georgia State University campus survival knowledge — the practical, student-centered information that lives scattered across official websites, Reddit threads, and word of mouth, and is hard to find quickly through official GSU channels.

**Why this knowledge is hard to find otherwise:** Official GSU websites are dense, siloed by department, and hard to navigate. A student trying to figure out what to do about a PAWS hold has to know which office to contact, find the right page, and parse formal university language — when the real answer is two sentences. This system makes that knowledge instantly searchable.

**Document Sources (10 total):**

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
| `docs/student_reviews.txt` | Real student reviews of campus life and academics | Student reviews + community knowledge |
| `docs/safety_downtown.txt` | Downtown Atlanta safety, LiveSafe app, MARTA safety | safety.gsu.edu + student knowledge |

---

## Chunking Strategy and Reasoning

**Chunk size:** 400 characters  
**Overlap:** 50 characters  
**Method:** Character-based sliding window implemented in `ingest.py`

**Why these numbers fit my documents:**  
My documents are a mix of structured step-by-step guides and short student advice paragraphs. Key facts tend to appear in 2–4 sentence bursts — for example, the steps for getting a MARTA pass fit comfortably in about 400 characters. This size is large enough to capture one complete idea without merging unrelated topics into the same chunk, which would dilute the embedding and hurt retrieval accuracy.

The 50-character overlap ensures that if a key fact spans a chunk boundary — for example, a numbered step that starts at the end of one chunk and finishes at the start of the next — at least one of the two chunks will contain enough context to be retrievable.

Chunks smaller than ~150 characters would produce fragments like "Check your PAWS account" with no context, making them impossible to match to specific queries. Chunks larger than ~800 characters would dilute embeddings by covering too many topics at once.

---

## Sample Chunks (5 labeled examples)

**Chunk 1 — Source: marta_upass.txt**
```
MARTA Pass Pricing for GSU Students:
- Monthly Pass (Calendar Month): $61 via the Parking Portal
- This is significantly cheaper than the standard MARTA monthly pass price

How to Get Your Discounted MARTA Pass:
1. Log in to the GSU Parking Portal at parking.gsu.edu
```

**Chunk 2 — Source: paws_guide.txt**
```
Holds on Your Account:
A hold on your PAWS account will prevent you from registering for classes. Common reasons for holds include:
- Not updating your emergency contact information (this is required every semester)
- Unpaid tuition balance
- Missing financial aid documents
```

**Chunk 3 — Source: financial_aid.txt**
```
Accepting Your Award in PAWS:
- Go to paws.gsu.edu and log in
- Select the Finances tab
- Federal grants (like Pell Grant) are automatically accepted for you
- Federal work-study and federal loans require you to manually accept them
- Do NOT accept aid for semesters you will not be enrolled in
```

**Chunk 4 — Source: safety_downtown.txt**
```
LiveSafe App:
The LiveSafe app is GSU's official safety app. Download it for free on iOS or Android. With LiveSafe you can send a tip to GSU Police about suspicious activity, request a safety escort if you need to walk somewhere at night, virtually walk with a friend
```

**Chunk 5 — Source: dining.txt**
```
The Commons gets extremely crowded between noon and 1:30 PM on weekdays — go before 11:30 AM or after 2 PM to avoid long waits.
Meal swipes at The Commons give you all-you-can-eat access — take advantage of this.
Dining Dollars roll over between fall and spring semesters but typically expire at the end of the academic year.
```

---

## Embedding Model and Tradeoffs

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`

This model runs entirely locally — no API key, no rate limits, no cost. It produces 384-dimension embeddings and performs well on short to medium-length English text, which matches my document type.

**Production tradeoffs I would consider:**
- **`text-embedding-3-small` (OpenAI):** Higher accuracy on domain-specific queries and supports longer context windows, but costs money per API call and requires internet access — not ideal for a free student tool
- **`multilingual-e5-large`:** Better for multilingual student populations (GSU has many international students), but heavier and slower to run locally
- **`all-mpnet-base-v2`:** Slightly more accurate than MiniLM but roughly 3x slower — acceptable for a small corpus like this but would not scale to millions of documents
- For a real production system serving thousands of GSU students daily, I would use an API-based embedding model for accuracy with caching to control cost, and monitor retrieval quality with user feedback signals

---

## Retrieval Test Results

**Query 1: "How do I get a discounted MARTA pass as a GSU student?"**

Top returned chunks:
- `marta_upass.txt` (distance: 0.18) — "Log in to the GSU Parking Portal at parking.gsu.edu, purchase your discounted monthly pass online, wait for a confirmation email..."
- `student_reviews.txt` (distance: 0.41) — "Get your MARTA UPass as soon as you arrive — it saves a lot of money on transportation..."

**Why these chunks are relevant:** The top result is directly from the MARTA guide and contains the exact steps. The second result is a student review mentioning the UPass, which adds context. Both are genuinely relevant to the query.

**Query 2: "What should I do if I have a hold on my PAWS account?"**

Top returned chunks:
- `paws_guide.txt` (distance: 0.21) — "Check your PAWS account to see if there is a contact person listed on the hold. Then email registrar@gsu.edu with details about the hold removal request..."
- `find_help.txt` (distance: 0.38) — "Hold on account related to finances: Check PAWS for the contact name listed on the hold, then email registrar@gsu.edu..."

**Why these chunks are relevant:** Both chunks directly address PAWS holds and give the same actionable advice (check PAWS, email the registrar). The system correctly retrieved two sources that reinforce each other.

**Query 3: "What safety resources does GSU offer for students in downtown Atlanta?"**

Top returned chunks:
- `safety_downtown.txt` (distance: 0.14) — "The LiveSafe app is GSU's official safety app. Download it for free on iOS or Android. With LiveSafe you can send a tip to GSU Police..."
- `find_help.txt` (distance: 0.35) — "Campus emergency: Call 911 first, then GSU Police at 404-413-3333. Non-emergency safety concern: Download the LiveSafe app..."

**Why these chunks are relevant:** The safety document is the primary source and ranks first with a very low distance score. The find_help document adds complementary safety contact information.

---

## How Grounded Generation is Enforced

Grounding is enforced through the system prompt in `query.py`. The prompt explicitly instructs the model:

> "Answer the student's question using ONLY the information provided in the documents below. If the documents do not contain enough information to answer the question, say exactly: 'I don't have enough information on that in my GSU guide.' Do not use any outside knowledge."

Source attribution is guaranteed programmatically — after retrieval, the source filenames are extracted from ChromaDB metadata and appended to every response regardless of what the LLM generates. This means sources are always shown even if the model forgets to cite them in its answer text.

---

## Example Responses with Source Attribution

**Example 1 — In-scope question:**

> **Q:** How do I accept my financial aid award at GSU?
>
> **A:** To accept your financial aid award at GSU, log into PAWS at paws.gsu.edu and select the Finances tab. Federal grants like the Pell Grant are automatically accepted for you. However, federal work-study and federal loans require you to manually accept them. Important: do not accept aid for semesters you will not be enrolled in. (Source: financial_aid.txt)
>
> **Retrieved from:** financial_aid.txt, paws_guide.txt

**Example 2 — In-scope question:**

> **Q:** Where do I go for academic advising as a new student?
>
> **A:** As a new student, you should attend New Student Orientation, where you will meet with academic advisors to plan your schedule and register for classes. You can also use the advisor search tool at advisement.gsu.edu to find your assigned advisor based on your college. For quick questions, use Panther Answers at gsu.my.site.com/support/s. (Source: advisement.txt)
>
> **Retrieved from:** advisement.txt, find_help.txt

**Example 3 — Out-of-scope refusal:**

> **Q:** What is the best pizza place in Atlanta?
>
> **A:** I don't have enough information on that in my GSU guide.
>
> **Retrieved from:** student_reviews.txt, dining.txt, safety_downtown.txt

---

## Query Interface

**Input field:** A text box labeled "Your Question" where students type a plain-language question. Pressing Enter or clicking the Ask button submits the query.

**Output fields:**
- **Answer:** A multi-line text box showing the grounded response generated by Groq's llama-3.3-70b-versatile model
- **Retrieved from:** A text box listing the source document filenames that were used to generate the answer

**Sample interaction transcript:**

```
Student: What dining options are available on campus and how do I avoid long lines?

Answer: Georgia State University has several dining options on the Atlanta campus,
including The Commons (main dining hall), Urban Grille, Panda Express, Chick-fil-A,
Starbucks, and Subway. The Commons gets extremely crowded between noon and 1:30 PM
on weekdays — go before 11:30 AM or after 2 PM to avoid long waits. Note that
Chick-fil-A is closed on Sundays. Meal swipes at The Commons give you all-you-can-eat
access. (Source: dining.txt)

Retrieved from:
• dining.txt
• student_reviews.txt
• find_help.txt
```

**To run the interface:**
```bash
source .venv/bin/activate
python3 app.py
# Open http://127.0.0.1:7860 in your browser
```

---

## Evaluation Report

| # | Question | Expected Answer | System Response | Accuracy |
|---|---|---|---|---|
| 1 | How do I get a discounted MARTA pass as a GSU student? | Log into GSU Parking Portal, buy $61 calendar month pass, wait for email, pick up Breeze Card at UBS Center | Correct steps in correct order, cited marta_upass.txt | ✅ Accurate |
| 2 | What should I do if I have a hold on my PAWS account? | Check PAWS for contact on hold, email registrar@gsu.edu, clear before registration | Correct advice, cited paws_guide.txt and find_help.txt | ✅ Accurate |
| 3 | How do I accept my financial aid award at GSU? | Log into PAWS → Finances tab, manually accept loans and work-study, Pell Grant auto-accepted | Correct and complete, cited financial_aid.txt | ✅ Accurate |
| 4 | Where do I go for academic advising as a new student? | Attend New Student Orientation, use advisor search at advisement.gsu.edu | Correct, cited advisement.txt | ✅ Accurate |
| 5 | What safety resources does GSU offer for students in downtown Atlanta? | LiveSafe app, emergency alerts at getrave.com/login/gsu, GSU Police at 404-413-3333 | Returned LiveSafe and emergency alerts but omitted the blue light emergency phones detail | ⚠️ Partially Accurate |

---

## Failure Case Analysis

**Question 5** (safety resources) was partially accurate. The system correctly identified the LiveSafe app and emergency alert signup but did not mention the blue light emergency phones located across campus, even though this information exists in `safety_downtown.txt`.

**Why it happened:** The blue light phone information appears near the end of the `safety_downtown.txt` document. When the text was chunked at 400-character intervals, the blue light section ended up in a chunk that also contained mental health crisis information. The embedding for that mixed chunk was pulled toward mental health content rather than physical safety infrastructure, so it ranked lower than the LiveSafe chunks for a query about "safety resources." The relevant detail was present in the documents but was not retrieved because its chunk's embedding was diluted by unrelated content.

**What I would fix:** Split the safety document into smaller thematic sections before chunking, so each chunk covers one safety topic rather than mixing physical safety and mental health resources in the same chunk.

---

## Spec Reflection

**One way the spec helped:** Writing the evaluation plan in `planning.md` before any code forced me to define 5 specific, answerable questions upfront. This made it easy to test retrieval quality at each stage — I had concrete queries to run rather than vague spot checks. It also revealed early that question 5 (safety resources) was harder to answer completely than the others, which helped me understand where the system's weaknesses were.

**One way implementation diverged from the spec:** My planning.md described chunking by paragraph structure for longer documents, but in practice the documents had inconsistent paragraph lengths. Some paragraphs were 800+ characters and others were under 50. I switched to a fixed character-based chunking approach (400 characters with 50 overlap) because it produced more consistent chunk sizes across all 10 documents. This was a better fit for the actual data even though it wasn't what I originally planned.

---

## AI Usage

**Instance 1 — Generating ingest.py:**  
I gave Claude my planning.md Chunking Strategy section and Documents section and asked it to implement a script that loads .txt files from a docs/ folder, cleans them by removing short lines and extra whitespace, and splits them into 400-character chunks with 50-character overlap. Claude generated a complete script. I reviewed it and added the `len(chunk_text) > 20` filter to skip tiny leftover chunks at the end of documents, which the generated code did not include.

**Instance 2 — Generating the grounding prompt in query.py:**  
I asked Claude to write a system prompt for the Groq LLM that strictly grounds answers to retrieved documents and returns a specific refusal phrase when the documents don't contain an answer. Claude generated a prompt that said "try to answer only from the documents." I strengthened the instruction to "answer using ONLY the information provided" and added the exact refusal phrase "I don't have enough information on that in my GSU guide" so the system's out-of-scope behavior would be consistent and testable.

---

## Setup and Running

```bash
# Clone and enter the project
git clone https://github.com/Sniggy26/ai201-project1-unofficial-guide-starter.git
cd ai201-project1-unofficial-guide-starter

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gradio python-dotenv

# Add your Groq API key
cp .env.example .env
# Edit .env and replace your_key_here with your Groq API key

# Build the vector store (run once)
python3 embed.py

# Launch the app
python3 app.py
# Open http://127.0.0.1:7860
```
