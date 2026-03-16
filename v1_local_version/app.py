import sys, os, json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from rag_engine import answer, init

import threading

# Initialize Engine in background to prevent slow startup
def background_init():
    print("AI Engine warming up...")
    init()
    print("AI Engine ready!")

threading.Thread(target=background_init, daemon=True).start()


app = Flask(__name__, static_folder=str(Path(__file__).parent), static_url_path='')

CORS(app)

@app.route('/')
def index():

    return send_from_directory(app.static_folder, 'index.html')


@app.route('/ask', methods=['POST'])
def ask():
    req = request.json
    query = req.get('query', '')
    if not query:
        return jsonify({"error": "No query"}), 400
    
    try:
        res = answer(query)
        # Ensure only serializable data
        return jsonify({
            "answer": res.get("answer", ""),
            "category": res.get("category", ""),
            "model": res.get("model", ""),
            "sources": [{"course": s.get("course",""), "text": s.get("text","")[:200]} for s in res.get("sources", [])]
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Full Stack API Server starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
