import requests

# Test the CORS headers on port 8001
url = "http://localhost:8001/auth/register"
headers = {
    "Content-Type": "application/json",
    "Origin": "http://localhost:5173"
}
data = {
    "email": "corstest2@test.com",
    "password": "test123"
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        if 'access-control' in key.lower():
            print(f"  {key}: {value}")
    print(f"\nResponse Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
