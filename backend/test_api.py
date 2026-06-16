import urllib.request
import json

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Health
    print("Testing /api/health...")
    try:
        response = urllib.request.urlopen(f"{base_url}/api/health")
        data = json.loads(response.read().decode('utf-8'))
        print("Success:", data)
    except Exception as e:
        print("Failed:", e)
        return

    # 2. Search
    print("\nTesting /api/search...")
    try:
        req_data = json.dumps({"query": "shivering and high fever with dry lips", "top_n": 3}).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/api/search", 
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        print("Success: Found matches:")
        for r in data:
            print(f"  - {r['disease']['roga']} (Score: {r['score']})")
    except Exception as e:
        print("Failed:", e)
        return

    # 3. Chat
    print("\nTesting /api/chat...")
    try:
        req_data = json.dumps({
            "message": "shivering and high fever with dry lips",
            "history": [],
            "api_key": None
        }).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/api/chat", 
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        print("Success: Chat Response:")
        clean_text = data['response'].encode('ascii', errors='replace').decode('ascii')
        print(clean_text)
        print("Offline mode:", data['offline_mode'])
    except Exception as e:
        print("Failed:", e)
        return

if __name__ == "__main__":
    test_api()
