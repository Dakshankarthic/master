
import sys, os
sys.path.append(os.path.join(os.getcwd(), "src"))
from rag_engine import answer, init, COURSE_MAP, search

init()

query = "courses"

print(f"Query: {query}")
result = answer(query)

print(f"Answer: {result['answer'].encode('ascii', 'ignore').decode('ascii')[:200]}...")

print(f"Category: {result.get('category')}")
print(f"Model: {result.get('model')}")

print("\n--- COURSE_MAP Check ---")
ql = query.lower()
for alias, full_name in COURSE_MAP.items():
    if alias in ql:
        print(f"Matched Alias: {alias} -> {full_name}")
        break

print("\n--- Search Check ---")
chunks = search(query)
print(f"Found {len(chunks)} chunks")
if chunks:
    for i, c in enumerate(chunks[:2]):
        print(f"Chunk {i} (Score: {c.get('score', 'N/A')}): {c['text'][:100]}...")
else:
    print("No chunks found in search!")
