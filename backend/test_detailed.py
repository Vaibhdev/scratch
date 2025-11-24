import requests
import json

# Test the registration endpoint in detail
url = "http://localhost:8000/auth/register"
headers = {
    "Content-Type": "application/json",
    "Origin": "http://localhost:5173"
}
data = {
    "email": "detailed_test@test.com",
    "password": "test123456"
}

print(f"Request URL: {url}")
print(f"Request Headers: {json.dumps(headers, indent=2)}")
print(f"Request Data: {json.dumps(data, indent=2)}")
print("\n" + "="*60 + "\n")

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"\nAll Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except requests.exceptions.RequestException as e:
    print(f"Request Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
