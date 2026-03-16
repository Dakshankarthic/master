# ============================================================
#  STEP 1 — Data Collection
#  File: src/scraper.py
#
#  Scrapes all MastersUnion course pages (17 courses × 5 tabs)
#  and saves clean text files to data/raw/
#
#  Run: python src/scraper.py
# ============================================================

import re
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# ── Config ──────────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://mastersunion.org"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── All courses with their tab URLs ─────────────────────────────────────────
# Pattern: BASE_URL + path = full URL
# Each course has up to 5 tabs — Overview, Curriculum, Admissions, Career, Class

COURSES = {

    # ── PGP Programmes ────────────────────────────────────────────────────
    "pgp_applied_ai": {
        "name": "PGP in Applied AI and Agentic Systems",
        "category": "pgp",
        "tabs": {
            "overview":   "/pgp-applied-ai-agentic-systems",
            "curriculum": "/pgp-applied-ai-agentic-systems-curriculum",
            "admissions": "/pgp-applied-ai-agentic-systems-admissions-and-fees",
            "career":     "/pgp-applied-ai-agentic-systems-career-prospects",
            "class":      "/pgp-applied-ai-agentic-systems-class-profile",
        },
    },
    "pgp_tbm": {
        "name": "PGP in Technology and Business Management",
        "category": "pgp",
        "tabs": {
            "overview":   "/pgp-technology-business-management",
            "curriculum": "/pgp-technology-business-management-curriculum",
            "admissions": "/pgp-technology-business-management-admissions-and-fees",
            "career":     "/pgp-technology-business-management-career-prospects",
            "class":      "/pgp-technology-business-management-class-profile",
        },
    },
    "pgp_hr": {
        "name": "PGP in Human Resources and Organisation Strategy",
        "category": "pgp",
        "tabs": {
            "overview":   "/pgp-human-resources-organisation-strategy",
            "curriculum": "/pgp-human-resources-organisation-strategy-curriculum",
            "admissions": "/pgp-human-resources-organisation-strategy-admissions-and-fees",
            "career":     "/pgp-human-resources-organisation-strategy-career-prospects",
            "class":      "/pgp-human-resources-organisation-strategy-class-profile",
        },
    },
    "pgp_sports": {
        "name": "PGP in Sports Management and Gaming",
        "category": "pgp",
        "tabs": {
            "overview":   "/pgp-sports-management-gaming",
            "curriculum": "/pgp-sports-management-gaming-curriculum",
            "admissions": "/pgp-sports-management-gaming-admissions-and-fees",
            "career":     "/pgp-sports-management-gaming-career-prospects",
            "class":      "/pgp-sports-management-gaming-class-profile",
        },
    },
    "pgp_uiux": {
        "name": "PGP in UI/UX and AI Product Design",
        "category": "pgp",
        "tabs": {
            "overview":   "/pgp-ui-ux-ai-product-design",
            "curriculum": "/pgp-ui-ux-ai-product-design-curriculum",
            "admissions": "/pgp-ui-ux-ai-product-design-admissions-and-fees",
            "career":     "/pgp-ui-ux-ai-product-design-career-prospects",
            "class":      "/pgp-ui-ux-ai-product-design-class-profile",
        },
    },
    "pgp_sustainability": {
        "name": "PGP in Sustainability and Business Management",
        "category": "pgp",
        "tabs": {
            "overview":   "/pgp-sustainability-business-management",
            "curriculum": "/pgp-sustainability-business-management-curriculum",
            "admissions": "/pgp-sustainability-business-management-admissions-and-fees",
            "career":     "/pgp-sustainability-business-management-career-prospects",
            "class":      "/pgp-sustainability-business-management-class-profile",
        },
    },

    # ── Executive Programmes ──────────────────────────────────────────────
    "pgp_capital_markets": {
        "name": "PGP in Capital Markets and Trading",
        "category": "executive",
        "tabs": {
            "overview":   "/pgp-in-capital-markets-and-trading",
            "curriculum": "/pgp-in-capital-markets-and-trading-curriculum",
            "admissions": "/pgp-in-capital-markets-and-trading-admissions-and-fees",
            "career":     "/pgp-in-capital-markets-and-trading-career-prospects",
        },
    },
    "pgp_entrepreneurship": {
        "name": "PGP in Entrepreneurship and Business Acceleration",
        "category": "executive",
        "tabs": {
            "overview":   "/pgp-in-entrepreneurship-business-acceleration",
            "curriculum": "/pgp-in-entrepreneurship-business-acceleration-curriculum",
            "admissions": "/pgp-in-entrepreneurship-business-acceleration-admissions-and-fees",
        },
    },
    "pgp_general_mgmt": {
        "name": "PGP Rise General Management",
        "category": "executive",
        "tabs": {
            "overview":   "/pgp-rise-general-management",
            "curriculum": "/pgp-rise-general-management-curriculum",
            "admissions": "/pgp-rise-general-management-admissions-and-fees",
        },
    },
    "pgp_general_mgmt_global": {
        "name": "PGP Rise General Management Global",
        "category": "executive",
        "tabs": {
            "overview":   "/pgp-rise-general-management-global",
            "curriculum": "/pgp-rise-general-management-global-curriculum",
            "admissions": "/pgp-rise-general-management-global-admissions-and-fees",
        },
    },

    # ── Family Business ───────────────────────────────────────────────────
    "pgp_opm": {
        "name": "PGP Rise Owners and Promoters Management",
        "category": "family_business",
        "tabs": {
            "overview":   "/pgp-rise-owners-promoters-management",
            "curriculum": "/pgp-rise-owners-promoters-management-curriculum",
            "admissions": "/pgp-rise-owners-promoters-management-admissions-and-fees",
        },
    },

    # ── UG Programmes ─────────────────────────────────────────────────────
    "ug_tbm": {
        "name": "UG in Technology and Business Management",
        "category": "ug",
        "tabs": {
            "overview":   "/ug-technology-business-management",
            "curriculum": "/ug-curriculum",
            "admissions": "/ug-admissions-and-fees",
            "career":     "/ug-career-prospects",
        },
    },
    "ug_psychology": {
        "name": "UG in Psychology and Marketing",
        "category": "ug",
        "tabs": {
            "overview":   "/ug-psychology-marketing",
            "admissions": "/ug-admissions-and-fees",
        },
    },
    "ug_data_science": {
        "name": "UG in Data Science and AI",
        "category": "ug",
        "tabs": {
            "overview":   "/ug-data-science-ai",
            "admissions": "/ug-admissions-and-fees",
        },
    },

    # ── Immersions ────────────────────────────────────────────────────────
    "pgp_bharat": {
        "name": "PGP Bharat",
        "category": "immersion",
        "tabs": {
            "overview":   "/pgp-bharat",
            "curriculum": "/pgp-bharat-curriculum",
            "admissions": "/pgp-bharat-admissions-and-fees",
        },
    },
}


# ── Text cleaner ─────────────────────────────────────────────────────────────

def clean_html(html: str, url: str = "") -> str:
    """Strip noise from HTML and return clean readable text."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove all noise elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "noscript", "iframe", "svg",
                     "button", "meta", "link", "picture", "video"]):
        tag.decompose()

    # Extract text
    text = soup.get_text(separator="\n")

    # Clean whitespace
    lines = [line.strip() for line in text.splitlines()]
    lines = [l for l in lines if l and len(l) > 3]

    # Deduplicate repeated nav-like lines
    seen = set()
    deduped = []
    for line in lines:
        normalised = line.lower().strip()
        if normalised not in seen:
            seen.add(normalised)
            deduped.append(line)

    # Remove excessive blank lines
    clean = re.sub(r"\n{3,}", "\n\n", "\n".join(deduped))
    return clean.strip()


# ── Single page fetcher with retry ───────────────────────────────────────────

def fetch_page(url: str, retries: int = 2) -> str:
    """Fetch a URL and return raw HTML. Returns empty string on failure."""
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 404:
                return ""
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(2 ** attempt)  # exponential backoff
            else:
                print(f"    [FAIL] {url} — {e}")
                return ""
    return ""


# ── Playwright fallback for JS-rendered pages ────────────────────────────────

def fetch_with_playwright(url: str) -> str:
    """
    Use only when fetch_page() returns thin content.
    Install: pip install playwright && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": HEADERS["User-Agent"]})
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2500)
            html = page.content()
            browser.close()
            return html
    except ImportError:
        print("    [INFO] Playwright not installed.")
        print("           Run: pip install playwright && playwright install chromium")
        return ""
    except Exception as e:
        print(f"    [FAIL] Playwright error: {e}")
        return ""


# ── PDF extractor ────────────────────────────────────────────────────────────

def extract_pdf(pdf_path: str, label: str) -> None:
    """Extract text from a downloaded PDF brochure."""
    import pdfplumber
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"  [SKIP] PDF not found: {pdf_path}")
        return

    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            t = page.extract_text()
            if t:
                parts.append(f"[Page {i}]\n{t}")

    text = "\n\n".join(parts).strip()
    out = RAW_DIR / f"{label}_brochure.txt"
    out.write_text(f"SOURCE: {pdf_path.name}\n\n{text}", encoding="utf-8")
    print(f"  [PDF] {pdf_path.name} → {out.name} ({len(text):,} chars)")


# ── Main scraper ─────────────────────────────────────────────────────────────

def scrape_all(use_playwright_fallback: bool = False) -> None:
    total   = sum(len(c["tabs"]) for c in COURSES.values())
    scraped = 0
    skipped = 0
    thin    = 0

    print(f"\nScraping {len(COURSES)} courses across ~{total} pages...")
    print("(polite 1.2s delay between requests)\n")

    for course_key, course in COURSES.items():
        name     = course["name"]
        category = course["category"]
        cat_dir  = RAW_DIR / category
        cat_dir.mkdir(exist_ok=True)

        print(f"── {name}")

        combined_parts = [
            f"COURSE: {name}",
            f"CATEGORY: {category}",
            f"SOURCE: mastersunion.org\n",
        ]

        for tab_name, path in course["tabs"].items():
            url  = BASE_URL + path
            html = fetch_page(url)

            # Thin content → try Playwright fallback
            if use_playwright_fallback and (not html or len(html) < 500):
                print(f"  [THIN] {tab_name} — trying Playwright...")
                html = fetch_with_playwright(url)

            if not html:
                print(f"  [SKIP] {tab_name:<14} (empty / 404)")
                skipped += 1
                time.sleep(1.2)
                continue

            text = clean_html(html, url)

            if len(text) < 150:
                print(f"  [THIN] {tab_name:<14} only {len(text)} chars — page may be JS-rendered")
                thin += 1
                time.sleep(1.2)
                continue

            # Save individual tab file
            tab_file = cat_dir / f"{course_key}_{tab_name}.txt"
            header   = f"COURSE: {name}\nTAB: {tab_name.upper()}\nURL: {url}\n\n"
            tab_file.write_text(header + text, encoding="utf-8")

            # Append to combined
            combined_parts.append(f"\n\n{'='*60}\n{tab_name.upper()}\n{'='*60}\n{text}")

            chars = len(text)
            print(f"  [OK]   {tab_name:<14} {chars:>6,} chars → {tab_file.name}")
            scraped += 1

            time.sleep(1.2)  # be polite

        # Save combined file — used by the RAG index builder
        combined_text = "\n".join(combined_parts)
        combined_file = RAW_DIR / f"{course_key}_full.txt"
        combined_file.write_text(combined_text, encoding="utf-8")
        print(f"  [FULL] combined → {combined_file.name}\n")

    # Summary
    all_files  = list(RAW_DIR.rglob("*.txt"))
    total_size = sum(f.stat().st_size for f in all_files)

    print("=" * 55)
    print(f"  Scraped : {scraped} pages")
    print(f"  Skipped : {skipped} pages (404 / network error)")
    print(f"  Thin    : {thin} pages (JS-rendered, needs Playwright)")
    print(f"  Files   : {len(all_files)} text files")
    print(f"  Total   : {total_size:,} bytes")
    print("=" * 55)

    if thin > 0:
        print(f"\n  {thin} pages were too thin (JS-rendered content).")
        print("  Re-run with: scrape_all(use_playwright_fallback=True)")
        print("  After: pip install playwright && playwright install chromium")

    print("\nNext step: python src/build_index.py")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  MastersUnion — Course Scraper  (Step 1)")
    print("=" * 55)

    # Set use_playwright_fallback=True if many pages come back THIN
    # Note: Requires 'pip install playwright && playwright install chromium'
    scrape_all(use_playwright_fallback=True)
