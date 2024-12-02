import time

import requests
from app.core.config import settings 

def query_huggingface_api_with_roles(system_message: str, user_message: str, retries=3, wait_time=10):
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "stream": False
    }

    API_URL = settings.API_URL
    HEADERS = {"Authorization": f"Bearer {settings.API_KEY}"}
    print("LLegue aqui", API_URL)
    for _ in range(retries):
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            print(f"Model not available. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            raise Exception(f"Request failed: {response.status_code}, {response.text}")
    
    raise Exception("Model not available after several attempts")