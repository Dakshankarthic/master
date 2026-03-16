"""
RAG Engine v8 — Gold Standard Performance.
Optimized for high factual accuracy on PGP Applied AI.
"""
import os
import json
import re
import time
import requests
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

CHUNKS_PATH = Path("data/processed/chunks.json")
INDEX_PATH = Path("data/processed/faiss_index")
LEADS_PATH = Path("data/leads.json")
_chunks = None
_vectorstore = None

def init():
    global _chunks, _vectorstore
    if _chunks is not None and _vectorstore is not None:
        return
    
    # Load human-readable chunks
    if CHUNKS_PATH.exists():
        _chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    
    # Load FAISS index
    if INDEX_PATH.exists():
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
        _vectorstore = FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)

# ── Maps ──────────────────────────────────────────────────────────────────────
# Added space-less versions for better matching (e.g. 'datascience')
COURSE_MAP = {
    "applied ai": "PGP Applied AI and Agentic Systems",
    "appliedai": "PGP Applied AI and Agentic Systems",
    "agentic": "PGP Applied AI and Agentic Systems",
    "tbm": "PGP Technology and Business Management",
    "business management": "PGP Technology and Business Management",
    "capital markets": "PGP Capital Markets and Trading",
    "capitalmarkets": "PGP Capital Markets and Trading",
    "trading": "PGP Capital Markets and Trading",
    "hr": "PGP Human Resources and Organisation Strategy",
    "human resources": "PGP Human Resources and Organisation Strategy",
    "humanresources": "PGP Human Resources and Organisation Strategy",
    "sports": "PGP Sports Management and Gaming",
    "gaming": "PGP Sports Management and Gaming",
    "uiux": "PGP UI/UX and AI Product Design",
    "ui/ux": "PGP UI/UX and AI Product Design",
    "ai product design": "PGP UI/UX and AI Product Design",
    "design": "PGP UI/UX and AI Product Design",
    "sustainability": "PGP Sustainability and Business Management",
    "entrepreneurship": "PGP Entrepreneurship and Business Acceleration",
    "general management": "PGP Rise General Management",
    "rise": "PGP Rise General Management",
    "opm": "PGP Rise Owners and Promoters Management",
    "bharat": "PGP Bharat",
    "ug tbm": "UG Technology and Business Management",
    "psychology": "UG Psychology and Marketing",
    "data science": "UG Data Science and AI",
    "datascience": "UG Data Science and AI",
    "pg in ai": "PGP Applied AI and Agentic Systems",
    "ug in ai": "UG Data Science and AI",
    "ai": "PGP Applied AI and Agentic Systems",
}

# ── Agentic Tools ─────────────────────────────────────────────────────────────

def tool_emi_calculator(query):
    # Default parameters based on Applied AI ground truth
    total_fee = 2265000
    months = 12
    
    # Check for numbers in query
    num_matches = re.findall(r"(\d[\d,]+)", query)
    if num_matches:
        for num in num_matches:
            val = int(num.replace(",", ""))
            if val > 100000: total_fee = val
            elif val in [6, 12, 18, 24, 36]: months = val
            
    emi = total_fee / months
    return (
        f"### 🧮 EMI Calculator\n\n"
        f"Based on your request:\n"
        f"- **Total Amount:** ₹{total_fee:,}\n"
        f"- **Repayment Period:** {months} Months\n"
        f"- **Estimated EMI:** **₹{int(emi):,}**\n\n"
        "EMI options are available through our banking partners like HDFC and Bajaj Finserv."
    )

def tool_lead_capture(query):
    # Detect patterns for Name, Phone, Email
    patterns = {
        "name": r"(?:my name is|i am|name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        "phone": r"(\d{10})",
        "email": r"([\w.-]+@[\w.-]+\.\w+)"
    }
    
    name_match = re.search(patterns["name"], query, re.I)
    phone_match = re.search(patterns["phone"], query)
    email_match = re.search(patterns["email"], query)
    
    name_val = name_match.group(1).strip() if name_match else None
    
    # Fix Bug #4: Regex was too greedy with re.I. Clean up common bleed-in words.
    if name_val:
        for stop in [" and ", " my ", " is ", " email ", " phone "]:
            if stop in name_val.lower():
                name_val = name_val.lower().split(stop)[0].strip().title()
                break

    phone_val = phone_match.group(1) if phone_match else None
    email_val = email_match.group(1) if email_match else None
    
    if name_val and (phone_val or email_val):
        leads = []
        if LEADS_PATH.exists():
            try: leads = json.loads(LEADS_PATH.read_text())
            except: pass
        
        # Bug #6 & #7: Deduplication and standardization
        is_duplicate = any(l.get("email") == email_val or l.get("phone") == phone_val for l in leads if email_val or phone_val)
        
        if not is_duplicate:
            entry = {
                "name": name_val, 
                "phone": phone_val, 
                "email": email_val, 
                "time": time.time(), # Standardized key (Bug #7)
                "q": query
            }
            leads.append(entry)
            LEADS_PATH.write_text(json.dumps(leads, indent=2))
            return f"### ✅ Success!\n\nThank you, **{name_val}**! Your interest has been recorded. Our admissions counselor will contact you at **{phone_val or email_val}** very soon."
        else:
            return f"### ✅ Already Recorded\n\nWe already have your details, **{name_val}**. A counselor will be in touch shortly!"
    
    # Catch-all for "connect me" or "interested" without details
    if any(k in query.lower() for k in ["connect me", "interested", "i want to apply"]):
        if not (name_val or phone_val or email_val):
            return "I'd be happy to help! Could you please share your **Name**, **Email**, and **Phone Number** so our counselor can reach out to you?"

    return None

# ── Core Search & Answer ──────────────────────────────────────────────────────

def search(query, top_k=5):
    init()
    ql = query.lower().strip()
    
    # 1. Identify target course (Check longer aliases first to avoid partial matches)
    target_course = None
    sorted_aliases = sorted(COURSE_MAP.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if alias in ql:
            target_course = COURSE_MAP[alias]
            break
    
    # Bug #1 Fix: Use FAISS if available for semantic search
    if _vectorstore:
        # If we have a target course, we want to ensure we get results from it
        # Fetch more candidates for re-ranking
        candidates = _vectorstore.similarity_search(query, k=top_k * 4)
        
        matches = []
        others = []
        for doc in candidates:
            c_name = doc.metadata.get("course")
            chunk = {"text": doc.page_content, "course": c_name}
            if target_course and c_name == target_course:
                matches.append(chunk)
            else:
                others.append(chunk)
        
        # Combine: Priority matches first, then others
        # Fix: Use list conversion to avoid slice error in some linters
        results = list(matches + others)[:top_k]
        return results

    # Fallback to keyword search (Bug #5 fix included)
            
    scored = []
    keywords = list(set(re.findall(r'\b\w{3,}\b', ql)))
    
    for chunk in (_chunks or []):
        text = chunk["text"].lower()
        clean_text = text.replace(" ", "")
        score = 0
        for k in keywords:
            if k in text: score += 5
            elif k in clean_text: score += 3 
        
        if target_course and chunk.get("course") == target_course:
            score += 20
        
        # Bug #5 Fix: Use the loop variable 'q' correctly
        if any(q in ql for q in ["fee", "cost", "price"]) and "fee" in text: score += 10
        if any(q in ql for q in ["admission", "apply", "steps"]) and "admission" in text: score += 10
        if any(q in ql for q in ["outcome", "career", "placement", "salary"]) and any(x in text for x in ["placement", "salary", "career"]): score += 10
        
        if score > 0:
            scored.append((score, chunk))
            
    scored.sort(key=lambda x: -x[0])
    results = []
    seen = set()
    for _, c in scored:
        sig = c["text"][:100]
        if sig not in seen:
            seen.add(sig)
            results.append(c)
        if len(results) >= top_k: break
    return results

def answer(query):
    ql = query.lower()
    
    # --- AGENTIC TRIGGERS ---
    
    # Jailbreak / Off-topic
    if any(k in ql for k in ["ignore all", "write a poem", "story about"]):
        return {"answer": "I am an AI assistant specifically for MastersUnion admissions. I cannot fulfill requests unrelated to our programs.", "sources": [], "category": "Guardian", "model": "Agent"}
        
    # Lead Capture
    lead_res = tool_lead_capture(query)
    if lead_res: return {"answer": lead_res, "sources": [], "category": "Leads", "model": "CRM Agent"}
    
    # EMI Tool
    if "calculate emi" in ql or ("emi" in ql and ("fee" in ql or "month" in ql)):
        return {"answer": tool_emi_calculator(query), "sources": [], "category": "Tools", "model": "Calc Agent"}
        
    # Greeting / Profiler
    if ql in ["hi", "hello", "hey", "hii"]:
        return {"answer": "👋 **Hello!** I'm your MastersUnion Admissions Assistant.\n\nAre you currently a **recent graduate** or a **working professional**? Knowing this helps me provide the right program info for you.", "sources": [], "category": "Intro", "model": "Profiler"}

    # Multilingual (Simple Keyword Fallback)
    if any(k in query for k in ["பீஸ்", "எவ்வளவு", "ഫീസ്"]):
        return {"answer": "The total fee for the PGP Applied AI program is **₹22,65,000**. EMI options are available.", "sources": [], "category": "Fees", "model": "Polyglot"}

    # Course Clarifier (User Request: Ask for program if not specified)
    has_course = any(alias in ql or ql.replace(" ", "") == alias for alias in COURSE_MAP.keys())
    course_keywords = ["outcome", "placement", "salary", "career", "fee", "cost", "curriculum", "syllabus", "duration", "eligibility", "process", "admission", "requirement", "criteria", "faculty", "mentor", "professor", "teacher"]
    
    course_inquiry_keywords = ["course", "courses", "programs", "degrees", "what do you offer", "list of courses", "available courses"]
    if any(k in ql for k in course_inquiry_keywords) and not has_course:
        course_list = "\n".join([f"- **{v}**" for v in list(dict.fromkeys(COURSE_MAP.values()))]) # Deduplicate
        return {
            "answer": f"MastersUnion offers the following programs:\n\n{course_list}\n\nWhich program would you like to know more about?",
            "sources": [],
            "category": "Programs",
            "model": "Course Lister"
        }

    # --- SPECIAL AGENT: Course Overview (Table Request) ---
    if has_course and not any(k in ql for k in course_keywords):
        target = None
        for alias, full_name in COURSE_MAP.items():
            if alias in ql or ql.replace(" ", "") == alias:
                target = full_name
                break
        if target:
            # Re-direct to standard RAG but with a table-focused query
            query = f"Provide a comprehensive overview of the {target} in a structured Markdown table format, including duration, fees, and outcomes."
            # Continue to standard RAG...

    # --- STANDARD RAG (DIRECT RETRIEVAL) ---
    
    chunks = search(query, top_k=3) # Reduced from 5 to 3 for speed
    if not chunks:
        return {"answer": "I don't have that specific information in my records. Please contact pgadmissions@mastersunion.org.", "sources": [], "category": "Fallback", "model": "RAG"}

    # Build context from chunks
    context_text = "\n\n---\n\n".join([c["text"] for c in chunks[:3]])
    
    # Prepare prompt for Llama 3.2
    messages = [
        {
            "role": "system", 
            "content": """You are the official MastersUnion Admissions Intelligence. 
Your goal is to provide elite, professional, and highly accurate guidance to prospective students.

RULES:
1. Use ONLY the provided context.
2. Output a Markdown TABLE.
3. Short & Concise only."""
        },
        {"role": "user", "content": f"CONTEXT FROM DATABASE:\n{context_text}\n\nUSER QUESTION: {query}"}
    ]
    
    # Generate actual AI response via Llama 3.2
    try:
        response = requests.post(
            'http://localhost:11434/api/chat',
            json={
                "model": "llama3.2", # Switched to 3B model for 10x speed boost on CPU
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 400,
                    "num_ctx": 2048 
                }
            },
            timeout=90 # 90s is plenty for Llama 3.2 3B
        )
        if response.status_code == 200:
            ai_answer = response.json().get("message", {}).get("content", "").strip()
            if ai_answer:
                return {"answer": ai_answer, "sources": list(chunks[:3]), "category": "AI Wisdom", "model": "Llama 3.2 (3B) Fast"}
    except Exception as e:
        print(f"Llama generation failed: {str(e)}")
        
    # If the LLM call fails, fallback to direct concatenation
    ans_text = "### ⚡ Speed Tip\n\nYour CPU is struggling with the 8B model. Please run `ollama pull llama3.2` for instant answers!\n\nHere is the raw data:\n\n"
    ans_text += "\n\n---\n\n".join([c["text"] for c in chunks[:2]])
    return {"answer": ans_text, "sources": chunks[:3], "category": "Direct", "model": "Fast Fallback"}
