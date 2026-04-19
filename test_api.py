import requests

url = "http://127.0.0.1:5000/submit"

data = {
    "response_time": 10,
    "attempts": 1,
    "confidence": 0.8,
    "is_application": 1,
    "correct": 0,

    "time_taken": 15,
    "idle_time": 5,
    "rewrite_count": 2,
    "backspace_count": 10,
    "skipped": 0
}

res = requests.post(url, json=data)
print(res.json())