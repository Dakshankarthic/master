import requests
import json
import time

def test_ollama():
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3:8b",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": False
    }
    
    print(f"Testing Ollama at {url}...")
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        duration = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Duration: {duration:.2f}s")
        
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error Response Body: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_ollama()
