# ============================================================
#  STEP 2 + 3 + 4 — Chunking → Embedding → FAISS Index
#  File: src/build_index.py
#
#  Reads all *_full.txt files from data/raw/
#  Splits them into 400-word overlapping chunks
#  Embeds each chunk with sentence-transformers (free, local)
#  Saves a searchable FAISS index to data/processed/
#
#  Run AFTER scraper.py:
#      python src/build_index.py
# ============================================================

import os
import json
import time
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_DIR   = Path("data/raw")
INDEX_DIR = Path("data/processed")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# ── Tuning (overridable via .env) ────────────────────────────────────────────
CHUNK_SIZE    = 400
CHUNK_OVERLAP = 60

# ── Course name lookup (filename stem → human-readable name) ─────────────────
COURSE_NAMES = {
    "pgp_applied_ai":          "PGP Applied AI and Agentic Systems",
    "pgp_tbm":                 "PGP Technology and Business Management",
    "pgp_hr":                  "PGP Human Resources and Organisation Strategy",
    "pgp_sports":              "PGP Sports Management and Gaming",
    "pgp_uiux":                "PGP UI/UX and AI Product Design",
    "pgp_sustainability":      "PGP Sustainability and Business Management",
    "pgp_capital_markets":     "PGP Capital Markets and Trading",
    "pgp_entrepreneurship":    "PGP Entrepreneurship and Business Acceleration",
    "pgp_general_mgmt":        "PGP Rise General Management",
    "pgp_general_mgmt_global": "PGP Rise General Management Global",
    "pgp_opm":                 "PGP Rise Owners and Promoters Management",
    "pgp_bharat":              "PGP Bharat",
    "ug_tbm":                  "UG Technology and Business Management",
    "ug_psychology":           "UG Psychology and Marketing",
    "ug_data_science":         "UG Data Science and AI",
}

TAB_LABELS = {
    "overview":   "Program Overview",
    "curriculum": "Curriculum",
    "admissions": "Admissions and Fees",
    "career":     "Career Outcomes",
    "class":      "Class Profile",
    "full":       "Full Program Info",
    "brochure":   "Program Brochure",
}


def parse_filename(stem: str) -> tuple[str, str]:
    """
    'pgp_applied_ai_full'       -> ('PGP Applied AI...', 'Full Program Info')
    'pgp_applied_ai_curriculum' -> ('PGP Applied AI...', 'Curriculum')
    """
    for key in sorted(COURSE_NAMES.keys(), key=len, reverse=True):
        if stem.startswith(key):
            tab_key     = stem[len(key):].lstrip("_") or "full"
            course_name = COURSE_NAMES[key]
            tab_label   = TAB_LABELS.get(tab_key, tab_key.replace("_", " ").title())
            return course_name, tab_label
    return stem.replace("_", " ").title(), "General"


# ── Step 1: Load documents ────────────────────────────────────────────────────

def load_documents() -> list[dict]:
    """
    Load *_full.txt combined files from data/raw/.
    Using the combined file (all tabs merged) gives the RAG engine
    richer cross-tab context per chunk.
    """
    docs = []
    # Load both combined full text and extracted PDF brochures
    patterns = ["*_full.txt", "*_brochure.txt"]

    found_files = []
    for p in patterns:
        found_files.extend(list(RAW_DIR.rglob(p)))

    for txt_file in sorted(found_files):
        content = txt_file.read_text(encoding="utf-8").strip()

        if len(content) < 100:
            print(f"  [SKIP] {txt_file.name} — too short ({len(content)} chars)")
            continue

        course_name, tab_label = parse_filename(txt_file.stem)
        category = txt_file.parent.name if txt_file.parent != RAW_DIR else "general"

        docs.append({
            "content":  content,
            "source":   txt_file.name,
            "course":   course_name,
            "tab":      tab_label,
            "category": category,
        })

        try:
            print(f"  [LOAD] {txt_file.name:<50} {len(content):>7,} chars  [{course_name}]")
        except UnicodeEncodeError:
            print(f"  [LOAD] {txt_file.name}")

    return docs


# ── Step 2: Chunk documents ───────────────────────────────────────────────────

def chunk_documents(docs: list[dict]) -> tuple[list[str], list[dict]]:
    """
    Split each document into overlapping chunks.
    400 words, 60-word overlap = each chunk is a self-contained idea,
    overlap prevents answers from being cut mid-sentence.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )

    all_texts   = []
    all_metas   = []
    seen_chunks = set()  # Global dedup

    for doc in docs:
        chunks = splitter.split_text(doc["content"])
        for i, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if len(chunk) < 60:      # discard tiny fragments
                continue
            
            # Use a hash or first/last slice for dedup
            sig = chunk[:150] + chunk[-150:]
            if sig in seen_chunks:
                continue
            seen_chunks.add(sig)

            all_texts.append(chunk)
            all_metas.append({
                "source":   doc["source"],
                "course":   doc["course"],
                "tab":      doc["tab"],
                "category": doc["category"],
                "chunk_id": i,
            })

    courses_covered = len({m["course"] for m in all_metas})
    avg_len = sum(len(t) for t in all_texts) // max(len(all_texts), 1)
    print(f"\n  Total chunks : {len(all_texts)}")
    print(f"  Avg length   : {avg_len} chars")
    print(f"  Courses      : {courses_covered}")

    return all_texts, all_metas


# ── Step 3 + 4: Embed + build FAISS index ────────────────────────────────────

def build_faiss_index(texts: list[str], metas: list[dict]) -> None:
    """
    Embed every chunk using sentence-transformers (free, local, no API key).
    Store vectors in FAISS for millisecond-speed retrieval.

    Why all-MiniLM-L6-v2:
      - 384-dimensional vectors (fast search)
      - Top-tier semantic similarity performance for its size
      - Runs on CPU — no GPU needed
      - Completely free, no rate limits
    """
    print("\n── Loading embedding model (sentence-transformers/all-MiniLM-L6-v2) ──")
    print("   First run downloads ~90MB model. Subsequent runs use cache.")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("   Model ready.\n")

    print(f"── Embedding {len(texts)} chunks and building FAISS index ──")
    print("   This takes 1-4 minutes on CPU. Go grab water.")
    t0 = time.time()

    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metas,
    )

    elapsed = round(time.time() - t0, 1)
    print(f"   Done in {elapsed}s")

    # Save FAISS index
    index_path = INDEX_DIR / "faiss_index"
    vectorstore.save_local(str(index_path))
    print(f"\n   Index saved → {index_path}/")

    # Save human-readable chunks (for citation display in UI)
    chunks_data = [{"text": t, **m} for t, m in zip(texts, metas)]
    chunks_path = INDEX_DIR / "chunks.json"
    chunks_path.write_text(json.dumps(chunks_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   Chunks saved → {chunks_path}")

    # Save index stats (shown in sidebar)
    stats = {
        "total_chunks":  len(texts),
        "courses":       sorted({m["course"] for m in metas}),
        "categories":    sorted({m["category"] for m in metas}),
        "chunk_size":    CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "embed_model":   "sentence-transformers/all-MiniLM-L6-v2",
        "build_time_s":  elapsed,
    }
    stats_path = INDEX_DIR / "index_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"   Stats saved  → {stats_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  Index Builder  (Steps 2 + 3 + 4)")
    print("=" * 55)

    print("\n── Loading raw documents ──")
    docs = load_documents()

    if not docs:
        print("\n[ERROR] No *_full.txt files found in data/raw/")
        print("Run python src/scraper.py first.")
        raise SystemExit(1)

    print(f"\n  Loaded {len(docs)} course documents")

    print("\n── Chunking documents ──")
    texts, metas = chunk_documents(docs)

    print("\n── Building FAISS index ──")
    build_faiss_index(texts, metas)

    print("\n" + "=" * 55)
    print("  Index built successfully!")
    print("  Next step: streamlit run app.py")
    print("=" * 55)
