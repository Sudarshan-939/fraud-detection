import requests
import json

def test_analyze():
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/analyze',
            json={"text": "The Earth is flat"},
            timeout=10
        )
        print("Status code:", response.status_code)
        try:
            print("Response JSON:", json.dumps(response.json(), indent=2))
        except:
            print("Response:", response.text)
    except Exception as e:
        print("Exception:", str(e))

test_analyze()
