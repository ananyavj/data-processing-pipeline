#test_api.py
import requests

# Test the ingest endpoint
new_logs = [
    {
        "timestamp": "2024-01-25T15:00:00Z",
        "level": "ERROR",
        "message": "Payment failed for user bob@test.com from IP 203.0.113.5"
    },
    {
        "timestamp": "2024-01-25T15:01:00Z",
        "level": "WARNING",
        "message": "API key api_key=secret123 about to expire"
    }
]

# Ingest logs with source tag
response = requests.post(
    "http://localhost:8000/ingest?source=payment-service",
    json=new_logs
)

print("Ingest response:")
print(response.json())
print()

# Search for payment errors
search_response = requests.get(
    "http://localhost:8000/search",
    params={"q": "payment failed", "k": 3}
)

print("Search results for 'payment failed':")
for log in search_response.json():
    print(f"- [{log['level']}] {log.get('source', 'N/A')}: {log['message']}")
print()

# Get logs from specific source
logs_response = requests.get(
    "http://localhost:8000/logs",
    params={"source": "payment-service"}
)

print(f"Logs from 'payment-service' source ({len(logs_response.json())} total):")
for log in logs_response.json():
    print(f"- {log['message']}")
