import requests
import json

# Test the optimization endpoint
url = "http://localhost:8000/optimize"

payload = {
    "pod_id": "000011",
    "electricity_price": 0.30,
    "feed_in_tariff": 0.05,
    "budget": 10000,
    "max_shares_per_project": 50
}

print("Testing optimization endpoint...")
print(f"Request: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(json.dumps(result, indent=2))
    else:
        print(f"\nError {response.status_code}:")
        print(response.text)
        
except Exception as e:
    print(f"\nError: {e}")
    print("\nMake sure the server is running:")
    print("  python -m uvicorn main:app --reload")
