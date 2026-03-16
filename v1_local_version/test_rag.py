import sys
import os

from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from rag_engine import answer


query = "hi im want to do pg in ai and what is the program duration? how many months ? is it online or offline ?"
result = answer(query)
with open("test_out.txt", "w", encoding="utf-8") as f:

    f.write(f"QUERY: {query}\n")
    f.write("\n--- ANSWER ---\n")
    f.write(result["answer"])
    f.write("\n\n--- SOURCES (Top 1) ---\n")
    if result["sources"]:
        f.write(result["sources"][0]["text"][:500])
